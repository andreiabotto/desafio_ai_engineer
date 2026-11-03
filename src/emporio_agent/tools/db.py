"""Helpers compartilhados de acesso ao SQLite pelas tools."""

from __future__ import annotations

from pathlib import Path

from emporio_agent.config import DB_PATH
from emporio_agent.data.ingest_csv import db_ready, get_connection, ingest_csvs

_active_db: Path | None = None


def set_db_path(path: Path | None) -> None:
    global _active_db
    _active_db = path


def resolve_db_path() -> Path:
    return _active_db or DB_PATH


def ensure_db() -> Path:
    path = resolve_db_path()
    if not db_ready(path):
        ingest_csvs(db_path=path)
    return path


def connect():
    return get_connection(ensure_db())