from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from emporio_agent.tools.datetime_tool import (
    format_store_clock_context,
    get_current_datetime,
    is_open_now,
    next_open_hint,
    now_store,
    store_clock_payload,
)

TZ = ZoneInfo("America/Campo_Grande")


def _dt(y: int, m: int, d: int, hh: int, mm: int = 0) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=TZ)


@pytest.mark.unit
def test_now_store_uses_injected_clock():
    frozen = _dt(2026, 3, 16, 10, 30)  # segunda
    assert now_store(now=frozen) == frozen


@pytest.mark.unit
def test_is_open_monday_morning():
    assert is_open_now(_dt(2026, 3, 16, 10, 0)) is True


@pytest.mark.unit
def test_is_closed_monday_evening():
    assert is_open_now(_dt(2026, 3, 16, 18, 0)) is False
    assert is_open_now(_dt(2026, 3, 16, 18, 1)) is False


@pytest.mark.unit
def test_is_closed_sunday():
    assert is_open_now(_dt(2026, 3, 15, 10, 0)) is False  # domingo


@pytest.mark.unit
def test_is_closed_saturday_afternoon():
    assert is_open_now(_dt(2026, 3, 14, 14, 0)) is False  # sábado 14h
    assert is_open_now(_dt(2026, 3, 14, 11, 0)) is True


@pytest.mark.unit
def test_is_closed_on_holiday():
    holiday = frozenset({"2026-03-16"})
    assert is_open_now(_dt(2026, 3, 16, 10, 0), holidays=holiday) is False


@pytest.mark.unit
def test_next_open_hint_sunday_to_monday():
    hint = next_open_hint(_dt(2026, 3, 15, 12, 0))
    assert hint is not None
    assert "segunda" in hint
    assert "09:00" in hint


@pytest.mark.unit
def test_store_clock_payload_includes_open_flag():
    payload = store_clock_payload(now=_dt(2026, 3, 16, 10, 0))
    assert payload["is_open_now"] is True
    assert payload["weekday"] == "segunda-feira"
    assert "next_open_hint" in payload


@pytest.mark.unit
def test_format_store_clock_context():
    text = format_store_clock_context(store_clock_payload(now=_dt(2026, 3, 15, 12, 0)))
    assert "fechada" in text
    assert "2026-03-15" in text


@pytest.mark.unit
def test_datetime_tool_shape():
    import json

    data = json.loads(get_current_datetime.invoke({}))
    assert "timezone" in data
    assert "weekday" in data
    assert "time" in data
    assert "is_open_now" in data
    assert isinstance(data["is_open_now"], bool)
