import pytest

from scripts.prepare_test_database import validate_test_database_url


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://localhost:5435/intelligent_orders",
        "postgresql+asyncpg://production:5434/intelligent_order_assistant_test",
        "postgresql+asyncpg://localhost:5434/production",
        "postgresql+asyncpg://localhost:5432/intelligent_order_assistant_test",
    ],
)
def test_destructive_guard_rejects_non_testing_destinations(url):
    with pytest.raises(RuntimeError):
        validate_test_database_url(url)


def test_destructive_guard_accepts_only_local_testing():
    validate_test_database_url(
        "postgresql+asyncpg://localhost:5434/intelligent_order_assistant_test"
    )
