"""Configuração de logging (CLI, Streamlit, Docker)."""

from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False


def setup_logging(level: str | None = None) -> None:
    """Idempotente: envia logs para stderr (visível em `docker compose logs`)."""
    global _CONFIGURED
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric = getattr(logging, level_name, logging.INFO)

    if _CONFIGURED:
        if level is not None:
            logging.getLogger().setLevel(numeric)
        return

    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
        force=True,
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
