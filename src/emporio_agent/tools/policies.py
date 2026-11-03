"""Tool de consulta às políticas da loja via RAG."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from emporio_agent.config import get_settings
from emporio_agent.data.ingest_policies import search_policy_chunks

_active_chroma: Path | None = None
_active_embeddings: Any | None = None


def set_chroma_dir(path: Path | None) -> None:
    global _active_chroma
    _active_chroma = path


def set_embeddings(embeddings: Any | None) -> None:
    global _active_embeddings
    _active_embeddings = embeddings


@tool
def search_policies(query: str) -> str:
    """Consulta o manual de políticas da Empório da Música.

    Use para horário, endereço, pagamento, trocas/devoluções, frete, garantia, LGPD e tom de atendimento.
    """
    cfg = get_settings()
    return search_policy_chunks(
        query,
        chroma_dir=_active_chroma,
        embeddings=_active_embeddings,
        k=cfg.rag_top_k,
    )
