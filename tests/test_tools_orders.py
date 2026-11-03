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
    assert "customer_name" in data["orders"][0]
    assert "email" not in data["orders"][0]
    assert "phone" not in data["orders"][0]
    assert "unit_price_brl" in data["orders"][0]["items"][0]


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


@pytest.mark.unit
def test_order_by_email_masks_name(temp_db):
    raw = get_order_status.invoke({"email": "lucas.mendes@jmail.com"})
    data = json.loads(raw)
    assert data["found"] is True
    name = data["orders"][0]["customer_name"]
    assert "***" in name
    assert "email" not in data["orders"][0]
    assert "phone" not in data["orders"][0]
    assert "notes" not in data["orders"][0]


@pytest.mark.unit
def test_order_by_phone_exact(temp_db):
    raw = get_order_status.invoke({"phone": "(67) 99812-3456"})
    data = json.loads(raw)
    assert data["found"] is True
    # customer_id 1 (Lucas) → pedido 4 nos CSVs atuais
    assert data["orders"][0]["order_id"] == 4
    assert "***" in data["orders"][0]["customer_name"]


@pytest.mark.unit
def test_order_short_phone_rejected(temp_db):
    raw = get_order_status.invoke({"phone": "123"})
    data = json.loads(raw)
    assert data["found"] is False
    assert "inválido" in data["message"].lower() or "incompleto" in data["message"].lower()


@pytest.mark.unit
def test_order_and_identifiers(temp_db):
    # order_id 1 + email errado → não encontra (AND)
    raw = get_order_status.invoke(
        {"order_id": 1, "email": "naoexiste@example.com"}
    )
    data = json.loads(raw)
    assert data["found"] is False


@pytest.mark.unit
def test_order_not_found(temp_db):
    raw = get_order_status.invoke({"order_id": 99999})
    data = json.loads(raw)
    assert data["found"] is False
