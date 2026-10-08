from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from langgraph.types import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.assistant import WorkflowError
from app.exceptions.order import OrderError
from app.graph.graph import create_assistant_graph
from app.repositories.assistant_run import AssistantRunRepository
from app.schemas.rag import RAGAnswerResponse
from app.services.order import OrderService
from app.services.rag import RAGService


class AssistantService:
    def __init__(
        self, session: AsyncSession, rag_service: RAGService, checkpointer
    ) -> None:
        self.checkpointer = checkpointer
        self.session = session
        self.orders = OrderService(session)
        self.runs = AssistantRunRepository(session)
        self.graph = create_assistant_graph(
            rag_service,
            self.orders,
            checkpointer=checkpointer,
            action_executor=self.execute_action,
        )

    async def ask(
        self, question: str, limit: int, requested_by: str
    ) -> RAGAnswerResponse:
        run_id = uuid4()
        result = await self.graph.ainvoke(
            {
                "question": question,
                "answer": "",
                "intent": "knowledge",
                "order_id": None,
                "order_action": None,
                "limit": limit,
                "max_distance": settings.rag_max_distance,
                "run_id": str(run_id),
            },
            {"configurable": {"thread_id": str(run_id)}},
        )
        if result.get("__interrupt__"):
            preview = result["__interrupt__"][0].value
            run = await self.runs.create(
                id=run_id,
                requested_by=requested_by,
                order_id=preview["order_id"],
                action=preview["action"],
                preview=preview,
                expires_at=datetime.now(timezone.utc)
                + timedelta(seconds=settings.approval_ttl_seconds),
            )
            await self.session.commit()
            return RAGAnswerResponse(
                answer="La acción requiere aprobación de un revisor.",
                run_id=run.id,
                status="pending_approval",
                approval=preview,
            )
        return RAGAnswerResponse(answer=result["answer"])

    async def review(self, run_id: UUID) -> RAGAnswerResponse:
        run = await self.runs.get(run_id)
        if run is None:
            raise WorkflowError("Solicitud no encontrada", 404)
        return RAGAnswerResponse(
            answer=run.answer or "La acción requiere aprobación de un revisor.",
            run_id=run.id,
            status="expired"
            if run.status == "pending_approval"
            and run.expires_at <= datetime.now(timezone.utc)
            else run.status,
            approval=run.preview,
        )

    async def decide(
        self, run_id: UUID, approve: bool, reviewer: str
    ) -> RAGAnswerResponse:
        # Session advisory lock survives commits and serializes graph resumes across
        # workers. It uses the checkpointer's dedicated connection, not a pool lease.
        async with self.checkpointer.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT pg_advisory_lock(hashtextextended(%s, 0))", (str(run_id),)
            )
        try:
            return await self._decide(run_id, approve, reviewer)
        finally:
            async with self.checkpointer.conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT pg_advisory_unlock(hashtextextended(%s, 0))", (str(run_id),)
                )

    async def _decide(
        self, run_id: UUID, approve: bool, reviewer: str
    ) -> RAGAnswerResponse:
        run = await self.runs.get(run_id, lock=True)
        if run is None:
            raise WorkflowError("Solicitud no encontrada", 404)
        if run.requested_by == reviewer:
            raise WorkflowError("El solicitante no puede aprobar su propia acción", 403)
        if run.status in {"completed", "rejected", "failed"}:
            if run.decision != approve:
                raise WorkflowError("La solicitud ya tiene una decisión diferente")
            return await self.review(run_id)
        if run.expires_at <= datetime.now(timezone.utc):
            raise WorkflowError("La aprobación ha expirado", 410)
        if run.decision is not None and run.decision != approve:
            raise WorkflowError("La solicitud ya tiene una decisión diferente")
        run.decision = approve
        run.approved_by = reviewer
        if not approve:
            run.status = "rejected"
            run.answer = "Acción rechazada; la orden no fue modificada."
        # Persist the decision before resuming. A retry after a crash can recover it.
        await self.session.commit()
        config = {"configurable": {"thread_id": str(run_id)}}
        snapshot = await self.graph.aget_state(config)
        if not snapshot.next:
            # The durable business result is authoritative if checkpoint completion
            # and the HTTP response were separated by a crash.
            run = await self.runs.get(run_id, lock=True)
            if run.status in {"completed", "rejected", "failed"}:
                return await self.review(run_id)
            raise WorkflowError("El flujo no está disponible para reanudación")
        result = await self.graph.ainvoke(Command(resume=approve), config)
        if not approve:
            run = await self.runs.get(run_id, lock=True)
            run.status = "rejected"
            run.answer = result["answer"]
            await self.session.commit()
        return await self.review(run_id)

    async def execute_action(self, run_id: str) -> str:
        run = await self.runs.get(UUID(run_id), lock=True)
        if run is None or run.decision is not True or run.approved_by != "reviewer":
            raise WorkflowError("Aprobación válida requerida", 403)
        if run.status in {"completed", "failed"}:
            return run.answer
        if run.expires_at <= datetime.now(timezone.utc):
            raise WorkflowError("La aprobación ha expirado", 410)
        order = await self.orders.order_repository.get_by_id_for_update(run.order_id)
        if order is None:
            raise WorkflowError("Orden no encontrada", 404)
        if (
            order.status != run.preview["status"]
            or order.updated_at.isoformat() != run.preview["updated_at"]
        ):
            run.status = "failed"
            run.answer = (
                "La orden cambió desde la solicitud; solicita una nueva aprobación."
            )
        else:
            try:
                if run.action == "confirm":
                    order = await self.orders.confirm_order(run.order_id, commit=False)
                elif run.action == "cancel":
                    order = await self.orders.cancel_order(run.order_id, commit=False)
                else:
                    raise WorkflowError("Acción no permitida")
            except OrderError as exc:
                raise WorkflowError(str(exc)) from exc
            run.status = "completed"
            run.answer = (
                f"Orden {order.id}: estado {order.status}, total ${order.total}."
            )
        # Action and replay receipt commit together; retries never apply stock twice.
        await self.session.commit()
        return run.answer
