import pytest
from pydantic import ValidationError

from app.schemas.order import OrderCreate


def test_create_valid_order() -> None:
    order = OrderCreate(
        customer_id=1,
        items=[
            {
                "product_id": 1,
                "quantity": 2,
            }
        ],
    )

    assert order.customer_id == 1
    assert len(order.items) == 1
    assert order.items[0].product_id == 1
    assert order.items[0].quantity == 2


def test_order_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(
            customer_id=1,
            items=[],
        )


def test_order_item_quantity_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(
            customer_id=1,
            items=[
                {
                    "product_id": 1,
                    "quantity": 0,
                }
            ],
        )


def test_order_customer_id_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(
            customer_id=0,
            items=[
                {
                    "product_id": 1,
                    "quantity": 1,
                }
            ],
        )
