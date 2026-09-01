from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate


def test_create_valid_product() -> None:
    product = ProductCreate(
        sku="LAPTOP-001",
        name="Laptop",
        description="Development laptop",
        price=Decimal("25000.00"),
        stock=10,
    )

    assert product.sku == "LAPTOP-001"
    assert product.price == Decimal("25000.00")
    assert product.stock == 10


def test_product_price_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(
            sku="LAPTOP-001",
            name="Laptop",
            price=Decimal("-100.00"),
            stock=10,
        )


def test_product_stock_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        ProductCreate(
            sku="LAPTOP-001",
            name="Laptop",
            price=Decimal("25000.00"),
            stock=-1,
        )
