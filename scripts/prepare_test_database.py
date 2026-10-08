"""Create pgvector only after validating both URL and the connected test database."""

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


def validate_test_database_url(url: str) -> None:
    parsed = make_url(url)
    if (
        parsed.database != "intelligent_order_assistant_test"
        or parsed.host not in {"localhost", "127.0.0.1"}
        or parsed.port != 5434
        or parsed.drivername != "postgresql+asyncpg"
    ):
        raise RuntimeError("Refusing destructive tests outside the local test database")


async def main() -> None:
    url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5434/intelligent_order_assistant_test",
    )
    validate_test_database_url(url)
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            if (
                await connection.scalar(text("SELECT current_database()"))
                != "intelligent_order_assistant_test"
            ):
                raise RuntimeError("Unexpected database")
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
