import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate


def test_create_valid_customer() -> None:
    customer = CustomerCreate(
        name="Miguel Lopez",
        email="miguel@example.com",
    )

    assert customer.name == "Miguel Lopez"
    assert customer.email == "miguel@example.com"


def test_customer_requires_valid_email() -> None:
    with pytest.raises(ValidationError):
        CustomerCreate(
            name="Miguel Lopez",
            email="not-an-email",
        )
