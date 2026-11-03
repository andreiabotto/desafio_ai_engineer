import json

import pytest

from emporio_agent.tools.products import get_product_by_name, search_products


@pytest.mark.unit
def test_search_products_max_price(temp_db):
    raw = search_products.invoke({"query": "violão", "max_price": 1000})
    data = json.loads(raw)
    assert data["count"] >= 1
    assert all(float(p["price_brl"]) <= 1000 for p in data["results"])


@pytest.mark.unit
def test_get_product_by_name_found(temp_db):
    raw = get_product_by_name.invoke({"name": "Yamaha C40"})
    data = json.loads(raw)
    assert data["found"] is True
    assert any("Yamaha C40" in m["name"] for m in data["matches"])


@pytest.mark.unit
def test_get_product_by_name_missing(temp_db):
    raw = get_product_by_name.invoke({"name": "Produto Inexistente XYZ"})
    data = json.loads(raw)
    assert data["found"] is False
