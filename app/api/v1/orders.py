from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionDep
from app.exceptions.order import OrderError
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreate,
    session: SessionDep,
) -> OrderResponse:
    service = OrderService(session)

    try:
        return await service.create_order(data)
    except OrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: int,
    session: SessionDep,
) -> OrderResponse:
    service = OrderService(session)

    order = await service.get_order(order_id)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


@router.get(
    "",
    response_model=list[OrderResponse],
)
async def list_orders(
    session: SessionDep,
) -> list[OrderResponse]:
    service = OrderService(session)

    return await service.list_orders()
