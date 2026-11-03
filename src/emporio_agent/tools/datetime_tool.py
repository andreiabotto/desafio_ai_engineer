"""Tool de data/hora da loja (Campo Grande/MS)."""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from emporio_agent.config import get_settings

_WEEKDAYS_PT = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)


@tool
def get_current_datetime() -> str:
    """Retorna data, hora e dia da semana no fuso da loja (Campo Grande/MS).

    Use junto com search_policies para responder se a loja está aberta agora.
    """
    cfg = get_settings()
    try:
        tz = ZoneInfo(cfg.store_timezone)
    except Exception:  # noqa: BLE001
        tz = ZoneInfo("America/Campo_Grande")
    now = datetime.now(tz)
    return json.dumps(
        {
            "timezone": str(tz),
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "weekday": _WEEKDAYS_PT[now.weekday()],
            "weekday_index_mon0": now.weekday(),
        },
        ensure_ascii=False,
    )
