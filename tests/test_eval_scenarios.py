"""Evals ligados aos examples/ — contratos de prompt + tools reais."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from emporio_agent.agent.prompts import SYSTEM_PROMPT
from emporio_agent.tools.orders import get_order_status
from emporio_agent.tools.products import search_products
from emporio_agent.tools.promotions import get_active_promotions

CASES_PATH = Path(__file__).parent / "eval_cases.yaml"
TOOLS = {
    "get_order_status": get_order_status,
    "search_products": search_products,
    "get_active_promotions": get_active_promotions,
}


def _load_cases() -> list[dict]:
    return yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    return _load_cases()


@pytest.mark.unit
def test_eval_cases_file_loads(cases):
    assert len(cases) >= 5
    ids = {c["id"] for c in cases}
    assert "lgpd_sem_identificador" in ids
    assert "seguranca_jailbreak" in ids


@pytest.mark.unit
@pytest.mark.parametrize(
    "case",
    [c for c in _load_cases() if c.get("kind") == "prompt_contract"],
    ids=lambda c: c["id"],
)
def test_prompt_contracts(case):
    for needle in case["must_include_in_prompt"]:
        assert needle.lower() in SYSTEM_PROMPT.lower(), f"missing '{needle}' in SYSTEM_PROMPT"


@pytest.mark.unit
@pytest.mark.parametrize(
    "case",
    [c for c in _load_cases() if c.get("kind") == "tool_unit"],
    ids=lambda c: c["id"],
)
def test_tool_eval_cases(case, temp_db):
    tool = TOOLS[case["tool"]]
    raw = tool.invoke(case.get("args") or {})
    data = json.loads(raw) if raw.strip().startswith("{") else {"text": raw}
    expect = case.get("expect") or {}

    if "found" in expect:
        assert data["found"] is expect["found"]
    if "status" in expect:
        assert data["orders"][0]["status"] == expect["status"]
    if "min_count" in expect:
        assert data.get("count", len(data.get("results", []))) >= expect["min_count"]
    if "max_price" in expect:
        assert all(float(p["price_brl"]) <= expect["max_price"] for p in data["results"])
    if "out_of_scope" in expect:
        assert data.get("out_of_scope") is expect["out_of_scope"]
    if "pix_stackable" in expect:
        assert data.get("pix_stackable") is expect["pix_stackable"]


@pytest.mark.unit
def test_datetime_tool_shape():
    from emporio_agent.tools.datetime_tool import get_current_datetime

    data = json.loads(get_current_datetime.invoke({}))
    assert "timezone" in data
    assert "weekday" in data
    assert "time" in data
