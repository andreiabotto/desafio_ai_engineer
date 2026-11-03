"""Inicialização compartilhada (CLI, Streamlit, Docker)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from emporio_agent.agent.graph import build_agent
from emporio_agent.config import Settings, get_settings
from emporio_agent.data.ingest_csv import db_ready, ingest_csvs
from emporio_agent.data.ingest_policies import get_embeddings, ingest_policies, policies_ready
from emporio_agent.tools.policies import set_embeddings

LogFn = Callable[[str], None]


def ensure_data_ready(
    force: bool = False,
    log: LogFn | None = None,
    *,
    load_embeddings: bool = True,
) -> None:
    def _log(msg: str) -> None:
        if log:
            log(msg)

    if force or not db_ready():
        _log("Ingerindo CSVs → SQLite...")
        ingest_csvs()
    if force or not policies_ready():
        _log("Indexando políticas (embeddings locais — pode demorar na 1ª vez)...")
        ingest_policies(force=force)
        # ingest_policies já carrega embeddings; reutiliza singleton abaixo

    if load_embeddings:
        _log("Carregando modelo de embeddings...")
        set_embeddings(get_embeddings())


def bootstrap_agent(
    settings: Settings | None = None,
    *,
    force: bool = False,
    log: LogFn | None = None,
) -> tuple[Any, Settings]:
    cfg = settings or get_settings()
    ensure_data_ready(force=force, log=log, load_embeddings=True)
    return build_agent(settings=cfg), cfg
