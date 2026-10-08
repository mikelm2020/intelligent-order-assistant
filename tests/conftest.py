import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from scripts.prepare_test_database import validate_test_database_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/"
    "intelligent_order_assistant_test",
)
validate_test_database_url(TEST_DATABASE_URL)

# Establish safe defaults before importing the application, so even its default
# engine cannot point to development/production during a test run.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["OPENAI_API_KEY"] = "test-only-not-a-real-key"
os.environ["OPERATOR_API_KEY"] = "test-operator-key-00000000000000000"
os.environ["REVIEWER_API_KEY"] = "test-reviewer-key-00000000000000000"
os.environ["AI_PROVIDER"] = "openai"

from app.core.config import settings
from app.core.database import get_db
from app.graph.checkpointer import (
    checkpoint_conn_string,
    get_checkpointer,
)
from app.main import app
from app.models.base import Base

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

    async with AsyncPostgresSaver.from_conn_string(
        checkpoint_conn_string(TEST_DATABASE_URL)
    ) as saver:
        async with saver.conn.cursor() as cursor:
            await cursor.execute("SELECT current_database()")
            actual = (await cursor.fetchone())["current_database"]
            if actual != "intelligent_order_assistant_test":
                raise RuntimeError("Unexpected checkpoint database")
        await saver.setup()

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

    async def override_checkpointer():
        async with AsyncPostgresSaver.from_conn_string(
            checkpoint_conn_string(TEST_DATABASE_URL)
        ) as saver:
            yield saver

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_checkpointer] = override_checkpointer

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={
            "Authorization": "Bearer " + settings.operator_api_key.get_secret_value()
        },
    ) as client:
        yield client

    app.dependency_overrides.clear()
