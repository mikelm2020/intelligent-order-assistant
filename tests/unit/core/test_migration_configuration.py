from alembic.config import Config

from alembic import command
from app.core.config import settings


def test_offline_migrations_preserve_percent_encoded_database_url(monkeypatch, capsys):
    url = (
        "postgresql+asyncpg://test:synthetic%40password%25@localhost:5434/"
        "intelligent_order_assistant_test"
    )
    monkeypatch.setattr(settings, "database_url", url)
    config = Config("alembic.ini")

    # SQL generation exercises env.py without opening any database connection.
    command.upgrade(config, "head", sql=True)

    assert config.get_main_option("sqlalchemy.url") == url
    output = capsys.readouterr().out
    assert "CREATE TABLE assistant_runs" in output
    assert "synthetic" not in output
