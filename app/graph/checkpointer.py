from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.engine import make_url

from app.core.config import settings


def checkpoint_conn_string(database_url: str) -> str:
    return (
        make_url(database_url)
        .set(drivername="postgresql")
        .render_as_string(hide_password=False)
    )


@asynccontextmanager
async def checkpoint_context():
    # Schema setup is an explicit deployment step, never a request-time migration.
    async with AsyncPostgresSaver.from_conn_string(
        checkpoint_conn_string(settings.database_url)
    ) as saver:
        yield saver


async def get_checkpointer():
    # FastAPI requires a plain yield dependency, not an asynccontextmanager wrapper.
    async with checkpoint_context() as saver:
        yield saver
