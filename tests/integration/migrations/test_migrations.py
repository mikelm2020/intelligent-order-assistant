import asyncio

from alembic.config import Config
from sqlalchemy import inspect, text

from alembic import command
from app.core.config import settings
from app.models.base import Base
from tests.conftest import TEST_DATABASE_URL, test_engine, validate_test_database_url


async def test_migrations_upgrade_downgrade_and_upgrade(monkeypatch):
    validate_test_database_url(TEST_DATABASE_URL)
    monkeypatch.setattr(settings, "database_url", TEST_DATABASE_URL)
    async with test_engine.begin() as connection:
        assert (
            await connection.scalar(text("SELECT current_database()"))
            == "intelligent_order_assistant_test"
        )
        await connection.run_sync(Base.metadata.drop_all)
        await connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    config = Config("alembic.ini")
    await asyncio.to_thread(command.upgrade, config, "head")
    async with test_engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
        assert set(Base.metadata.tables) <= set(tables)
        version = await connection.scalar(
            text("SELECT version_num FROM alembic_version")
        )
        assert version == "20261007_assistant_runs"
    await asyncio.to_thread(command.check, config)
    await asyncio.to_thread(command.downgrade, config, "base")
    await asyncio.to_thread(command.upgrade, config, "head")
    async with test_engine.begin() as connection:
        await connection.execute(text("DROP TABLE alembic_version"))
