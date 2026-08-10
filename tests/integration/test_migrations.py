import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_and_downgrade(tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    environment = os.environ.copy()
    environment["COMMERCE_OS_DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert "organizations" in tables
    assert "outbox_events" in tables
    assert "customer_signals" in tables
    assert "customer_voice_clusters" in tables
    assert "customer_insights" in tables
    assert "market_opportunities" in tables
    assert "opportunity_scores" in tables

    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0003_customer_intelligence"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    opportunity_downgrade = set(inspect(create_engine(database_url)).get_table_names())
    assert "market_opportunities" not in opportunity_downgrade
    assert "customer_signals" in opportunity_downgrade
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert "opportunity_risks" in set(inspect(create_engine(database_url)).get_table_names())

    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0002_governance_identity"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    downgraded_tables = set(inspect(create_engine(database_url)).get_table_names())
    assert "customer_signals" not in downgraded_tables
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    upgraded_tables = set(inspect(create_engine(database_url)).get_table_names())
    assert "customer_insights" in upgraded_tables

    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
