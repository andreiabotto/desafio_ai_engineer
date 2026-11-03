import json

import pytest

from emporio_agent.tools.orders import get_order_status


@pytest.mark.unit
def test_order_by_id(temp_db):
    raw = get_order_status.invoke({"order_id": 1})
    data = json.loads(raw)
    assert data["found"] is True
    assert data["orders"][0]["order_id"] == 1
    assert data["orders"][0]["tracking_code"].startswith("BR")


@pytest.mark.unit
def test_order_by_tracking(temp_db):
    raw = get_order_status.invoke({"tracking_code": "BRAB1234567BR"})
    data = json.loads(raw)
    assert data["found"] is True
    assert data["orders"][0]["status"] == "delivered"


@pytest.mark.unit
def test_order_missing_identifier(temp_db):
    raw = get_order_status.invoke({})
    data = json.loads(raw)
    assert data["found"] is False
