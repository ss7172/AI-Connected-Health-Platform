# pipeline/db.py
"""
Database connection and query execution utilities for the pipeline.
Uses SQLAlchemy Core (not ORM) for raw SQL performance.
"""
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Returns a singleton SQLAlchemy engine.
    Reads DATABASE_URL from environment.
    """
    global _engine
    if _engine is None:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise RuntimeError("DATABASE_URL not set in environment")
        _engine = create_engine(database_url, pool_pre_ping=True)
    return _engine


def get_connection() -> Connection:
    """Returns a new connection from the engine pool."""
    return get_engine().connect()


def load_sql(filename: str) -> str:
    """
    Load a SQL file from pipeline/sql/ directory.

    Args:
        filename: SQL filename e.g. 'revenue_analytics.sql'

    Returns:
        SQL string ready for execution
    """
    sql_dir = Path(__file__).parent / 'sql'
    sql_path = sql_dir / filename
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    return sql_path.read_text()


def execute_sql(sql: str, params: dict | None = None) -> list[dict[str, Any]]:
    """
    Execute a SQL query and return results as list of dicts.

    Args:
        sql: SQL string (may contain :param style placeholders)
        params: Optional dict of parameters

    Returns:
        List of row dicts
    """
    with get_connection() as conn:
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        conn.commit()
        return []


def execute_sql_file(filename: str, params: dict | None = None) -> list[dict[str, Any]]:
    """
    Load and execute a SQL file.

    Args:
        filename: SQL filename in pipeline/sql/
        params: Optional parameters

    Returns:
        List of row dicts
    """
    sql = load_sql(filename)
    return execute_sql(sql, params)


def create_analytics_schema() -> None:
    """
    Create the analytics schema and all destination tables.
    Safe to run multiple times — uses IF NOT EXISTS throughout.
    """
    sql = load_sql('create_schema.sql')
    with get_connection() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("Analytics schema created successfully.")