from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_tables(tmp_path, monkeypatch):
    database = tmp_path / "migrated.db"
    monkeypatch.setenv("APP_DISABLE_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database}")
    tables = set(inspect(engine).get_table_names())
    assert {"projects", "test_cases", "analyses", "app_settings", "alembic_version"} <= tables
