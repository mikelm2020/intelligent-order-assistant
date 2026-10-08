import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/"
    "intelligent_order_assistant_test",
)


def validate_test_database_url(url: str) -> None:
    parsed = make_url(url)
    if (
        parsed.database != "intelligent_order_assistant_test"
        or parsed.host not in {"localhost", "127.0.0.1"}
        or parsed.port != 5434
        or parsed.drivername != "postgresql+asyncpg"
    ):
        raise RuntimeError("Refusing destructive tests outside the local test database")


validate_test_database_url(TEST_DATABASE_URL)

# Ensure unit tests never need a real OpenAI key. No requests use this dummy key.
from app.core.config import settings

settings.openai_api_key = "test-only-not-a-real-key"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database(request):
    if not any(
        part in {"integration", "evaluation"} for part in request.node.path.parts
    ):
        yield
        return

    async with test_engine.begin() as connection:
        actual = await connection.scalar(text("SELECT current_database()"))
        if actual != "intelligent_order_assistant_test":
            raise RuntimeError("Refusing destructive tests: unexpected database")
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as connection:
        actual = await connection.scalar(text("SELECT current_database()"))
        if actual != "intelligent_order_assistant_test":
            raise RuntimeError("Refusing destructive tests: unexpected database")
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(prepare_database):
    async with TestSessionFactory() as session:
        yield session


@pytest_asyncio.fixture
async def client(prepare_database):
    async def override_get_db():
        async with TestSessionFactory() as db_session:
            yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
