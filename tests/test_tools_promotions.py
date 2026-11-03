import json
import sqlite3

import pytest

from emporio_agent.tools.promotions import get_active_promotions


@pytest.mark.unit
def test_active_promotions_only(temp_db):
    with sqlite3.connect(temp_db) as conn:
        # Conta produtos active com ao menos uma promo ativa (dedupe por product_id)
        active_products = conn.execute(
            """
            SELECT COUNT(DISTINCT pr.product_id)
            FROM promotions pr
            JOIN products p ON p.product_id = pr.product_id
            WHERE pr.is_active = 1 AND p.status = 'active'
            """
        ).fetchone()[0]

    raw = get_active_promotions.invoke({})
    data = json.loads(raw)
    assert data["count"] == active_products
    assert data["pix_stackable"] is False
    assert all(r.get("pix_stackable") is False for r in data["results"])


@pytest.mark.unit
def test_promo_price_math(temp_db):
    raw = get_active_promotions.invoke({})
    data = json.loads(raw)
    assert data["count"] >= 1
    for r in data["results"]:
        expected = round(float(r["price_brl"]) * (1 - float(r["discount_percent"]) / 100), 2)
        assert r["promo_price_brl"] == expected


@pytest.mark.unit
def test_promo_by_product_id(temp_db):
    raw = get_active_promotions.invoke({"product_id": 93})
    data = json.loads(raw)
    assert data["count"] <= 1
    if data["count"] == 1:
        assert data["results"][0]["product_id"] == 93
