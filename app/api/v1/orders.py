from fastapi import APIRouter, HTTPException, status

from app.api.error_handlers import handle_order_error
from app.core.database import SessionDep
from app.core.security import ReviewerDep
from app.exceptions.order import (
    OrderError,
)
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
        raise handle_order_error(exc) from exc


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


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
async def cancel_order(
    reviewer: ReviewerDep,
    order_id: int,
    session: SessionDep,
) -> OrderResponse:
    service = OrderService(session)

    try:
        return await service.cancel_order(order_id)

    except OrderError as exc:
        raise handle_order_error(exc) from exc


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
)
async def confirm_order(
    reviewer: ReviewerDep,
    order_id: int,
    session: SessionDep,
) -> OrderResponse:
    service = OrderService(session)

    try:
        return await service.confirm_order(order_id)

    except OrderError as exc:
        raise handle_order_error(exc) from exc
