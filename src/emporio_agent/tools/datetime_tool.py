"""Tool de data/hora da loja (Campo Grande/MS)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, time
from typing import Optional
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from emporio_agent.config import STORE_HOLIDAYS, STORE_WEEKLY_HOURS, get_settings

_WEEKDAYS_PT = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)


def store_tz(timezone_name: str | None = None) -> ZoneInfo:
    name = timezone_name or get_settings().store_timezone
    try:
        return ZoneInfo(name)
    except Exception:  # noqa: BLE001
        return ZoneInfo("America/Campo_Grande")


def now_store(
    *,
    timezone_name: str | None = None,
    now: datetime | None = None,
) -> datetime:
    """Relógio da loja; `now` permite testes determinísticos."""
    tz = store_tz(timezone_name)
    if now is None:
        return datetime.now(tz)
    if now.tzinfo is None:
        return now.replace(tzinfo=tz)
    return now.astimezone(tz)


def is_open_now(
    when: datetime,
    *,
    weekly_hours: dict[int, tuple[int, int, int, int] | None] | None = None,
    holidays: frozenset[str] | None = None,
) -> bool:
    hours = weekly_hours if weekly_hours is not None else STORE_WEEKLY_HOURS
    closed_days = holidays if holidays is not None else STORE_HOLIDAYS
    if when.strftime("%Y-%m-%d") in closed_days:
        return False
    window = hours.get(when.weekday())
    if window is None:
        return False
    open_h, open_m, close_h, close_m = window
    current = time(when.hour, when.minute, when.second)
    start = time(open_h, open_m)
    end = time(close_h, close_m)
    return start <= current < end


def next_open_hint(
    when: datetime,
    *,
    weekly_hours: dict[int, tuple[int, int, int, int] | None] | None = None,
    holidays: frozenset[str] | None = None,
) -> Optional[str]:
    """Próxima abertura a partir de `when` (inclusive se ainda for abrir hoje)."""
    hours = weekly_hours if weekly_hours is not None else STORE_WEEKLY_HOURS
    closed_days = holidays if holidays is not None else STORE_HOLIDAYS

    for day_offset in range(0, 8):
        day = when + timedelta(days=day_offset)
        date_key = day.strftime("%Y-%m-%d")
        if date_key in closed_days:
            continue
        window = hours.get(day.weekday())
        if window is None:
            continue
        open_h, open_m, _, _ = window
        open_at = day.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        if day_offset == 0 and when >= open_at:
            # Já passou a abertura de hoje — se ainda está aberto, hint é agora; senão próximo dia
            if is_open_now(when, weekly_hours=hours, holidays=closed_days):
                return (
                    f"aberta agora até "
                    f"{window[2]:02d}:{window[3]:02d} ({_WEEKDAYS_PT[day.weekday()]})"
                )
            continue
        if day_offset == 0 and when < open_at:
            return (
                f"{_WEEKDAYS_PT[day.weekday()]} {date_key} às "
                f"{open_h:02d}:{open_m:02d}"
            )
        if day_offset > 0:
            return (
                f"{_WEEKDAYS_PT[day.weekday()]} {date_key} às "
                f"{open_h:02d}:{open_m:02d}"
            )
    return None


def store_clock_payload(
    *,
    timezone_name: str | None = None,
    now: datetime | None = None,
) -> dict:
    current = now_store(timezone_name=timezone_name, now=now)
    tz = current.tzinfo
    open_now = is_open_now(current)
    return {
        "timezone": str(tz),
        "iso": current.isoformat(timespec="seconds"),
        "date": current.strftime("%Y-%m-%d"),
        "time": current.strftime("%H:%M"),
        "weekday": _WEEKDAYS_PT[current.weekday()],
        "weekday_index_mon0": current.weekday(),
        "is_open_now": open_now,
        "next_open_hint": next_open_hint(current),
        "hours_note": "seg–sex 09:00–18:00; sáb 09:00–13:00; dom/feriados fechado",
    }


def format_store_clock_context(payload: dict | None = None) -> str:
    data = payload or store_clock_payload()
    status = "aberta" if data["is_open_now"] else "fechada"
    hint = data.get("next_open_hint") or "sem previsão"
    return (
        f"Contexto temporal da loja ({data['timezone']}): "
        f"{data['weekday']} {data['date']} {data['time']} — "
        f"situação: {status}. Próxima abertura/referência: {hint}. "
        f"Horário padrão: {data['hours_note']}. "
        "Use estes dados para expediente e prazos; confirme detalhes de política com search_policies."
    )


@tool
def get_current_datetime() -> str:
    """Retorna data, hora, dia da semana e se a loja está aberta agora (fuso Campo Grande/MS).

    Use junto com search_policies para expediente, prazos e 'estamos abertos agora?'.
    """
    return json.dumps(store_clock_payload(), ensure_ascii=False)
