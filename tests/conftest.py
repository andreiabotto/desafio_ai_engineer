"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

from pathlib import Path

import pytest

from emporio_agent.config import CSV_FILES, POLICIES_PDF
from emporio_agent.data.ingest_csv import ingest_csvs
from emporio_agent.tools import db as db_tools
from emporio_agent.tools import policies as policy_tools


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test_emporio.db"
    ingest_csvs(db_path=db_path, csv_files=CSV_FILES)
    db_tools.set_db_path(db_path)
    yield db_path
    db_tools.set_db_path(None)


@pytest.fixture()
def policies_pdf() -> Path:
    assert POLICIES_PDF.exists()
    return POLICIES_PDF


@pytest.fixture()
def temp_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Chroma temporário — ingestão feita sob demanda nos testes de políticas."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    policy_tools.set_chroma_dir(chroma_dir)
    yield chroma_dir
    policy_tools.set_chroma_dir(None)
