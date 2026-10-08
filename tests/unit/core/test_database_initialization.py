from unittest.mock import AsyncMock, Mock

import pytest

from scripts import initialize_database, setup_checkpoints


def test_initialization_migrates_before_setting_up_checkpoints(monkeypatch):
    events = []

    def upgrade(config, revision):
        assert config.config_file_name == "alembic.ini"
        assert revision == "head"
        events.append("migrations")

    async def setup():
        events.append("checkpoints")

    monkeypatch.setattr(initialize_database.command, "upgrade", upgrade)
    monkeypatch.setattr(initialize_database, "setup_checkpoints", setup)

    initialize_database.main()

    assert events == ["migrations", "checkpoints"]


def test_failed_migration_does_not_initialize_checkpoints(monkeypatch):
    upgrade = Mock(side_effect=RuntimeError("Migration failed"))
    setup = AsyncMock()
    monkeypatch.setattr(initialize_database.command, "upgrade", upgrade)
    monkeypatch.setattr(initialize_database, "setup_checkpoints", setup)

    with pytest.raises(RuntimeError, match="Migration failed"):
        initialize_database.main()

    setup.assert_not_called()


def test_checkpoint_setup_failure_is_propagated(monkeypatch):
    monkeypatch.setattr(initialize_database.command, "upgrade", Mock())
    setup = AsyncMock(side_effect=RuntimeError("Checkpoint setup failed"))
    monkeypatch.setattr(initialize_database, "setup_checkpoints", setup)

    with pytest.raises(RuntimeError, match="Checkpoint setup failed"):
        initialize_database.main()

    setup.assert_awaited_once()


async def test_checkpoint_setup_uses_context_and_closes_on_error(monkeypatch):
    saver = Mock(setup=AsyncMock(side_effect=RuntimeError("Setup failed")))
    context = AsyncMock()
    context.__aenter__.return_value = saver
    context.__aexit__.return_value = False
    monkeypatch.setattr(setup_checkpoints, "checkpoint_context", lambda: context)

    with pytest.raises(RuntimeError, match="Setup failed"):
        await setup_checkpoints.main()

    saver.setup.assert_awaited_once()
    context.__aexit__.assert_awaited_once()
