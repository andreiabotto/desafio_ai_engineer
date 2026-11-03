"""Smoke tests opcionais contra a API real do Groq."""

from __future__ import annotations

import os

import pytest

from emporio_agent.agent.graph import build_agent, run_agent_turn
from emporio_agent.config import get_settings
from emporio_agent.data.ingest_csv import ingest_csvs
from emporio_agent.tools import db as db_tools


pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def live_db(tmp_path_factory):
    db = tmp_path_factory.mktemp("live") / "emporio.db"
    ingest_csvs(db_path=db)
    db_tools.set_db_path(db)
    yield db
    db_tools.set_db_path(None)


def test_live_simple_greeting(live_db):
    if not os.getenv("GROQ_API_KEY") and not get_settings().groq_api_key:
        pytest.skip("GROQ_API_KEY não configurada")

    agent = build_agent()
    answer, _ = run_agent_turn(agent, "Olá! Vocês são a Empório da Música?", history=[])
    assert len(answer) > 10
    assert any(
        token in answer.lower()
        for token in ["empório", "emporio", "música", "musica", "instrumento", "olá", "ola"]
    )
