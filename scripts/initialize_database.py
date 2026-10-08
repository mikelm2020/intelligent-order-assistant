"""Explicit deployment command: runs migrations on the configured database.

This module changes the schema. Verify DATABASE_URL and obtain authorization
before running it, especially against real data.
"""

import asyncio

from alembic.config import Config

from alembic import command
from scripts.setup_checkpoints import main as setup_checkpoints


def main() -> None:
    command.upgrade(Config("alembic.ini"), "head")
    asyncio.run(setup_checkpoints())


if __name__ == "__main__":
    main()
