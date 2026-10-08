"""Explicit schema setup. Verify DATABASE_URL and obtain authorization first."""

import asyncio

from app.graph.checkpointer import checkpoint_context


async def main() -> None:
    async with checkpoint_context() as saver:
        await saver.setup()


if __name__ == "__main__":
    asyncio.run(main())
