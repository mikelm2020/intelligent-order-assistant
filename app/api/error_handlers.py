from fastapi import HTTPException, status

from app.exceptions.order import (
    CustomerNotFoundError,
    InactiveProductError,
    InsufficientStockError,
    InvalidOrderStatusTransitionError,
    OrderAlreadyCancelledError,
    OrderAlreadyConfirmedError,
    OrderNotFoundError,
    ProductNotFoundError,
)


def handle_order_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            CustomerNotFoundError,
            ProductNotFoundError,
            OrderNotFoundError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        (
            InactiveProductError,
            InsufficientStockError,
            InvalidOrderStatusTransitionError,
            OrderAlreadyCancelledError,
            OrderAlreadyConfirmedError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected order error",
    )
