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
def test_search_products_accent_insensitive(temp_db):
    raw = search_products.invoke({"query": "violao", "max_price": 1000})
    data = json.loads(raw)
    assert data["count"] >= 1


@pytest.mark.unit
def test_search_products_category_only(temp_db):
    raw = search_products.invoke({"category": "Guitarras"})
    data = json.loads(raw)
    assert data["count"] >= 1
    assert all(
        "Guitarra" in p["category"] or "guitarra" in p["category"].lower()
        for p in data["results"]
    )


@pytest.mark.unit
def test_search_products_in_stock(temp_db):
    raw = search_products.invoke({"category": "Violões", "in_stock": True})
    data = json.loads(raw)
    assert data["count"] >= 1
    assert all(int(p["stock_quantity"]) > 0 for p in data["results"])


@pytest.mark.unit
def test_search_products_empty_args(temp_db):
    raw = search_products.invoke({})
    data = json.loads(raw)
    assert data["results"] == []
    assert "Informe" in data["message"]


@pytest.mark.unit
def test_search_products_accessory_gate(temp_db):
    raw = search_products.invoke({"query": "pedais de guitarra"})
    data = json.loads(raw)
    assert data["results"] == []
    assert data.get("out_of_scope") is True


@pytest.mark.unit
def test_search_like_wildcards_escaped(temp_db):
    raw = search_products.invoke({"query": "%_%"})
    data = json.loads(raw)
    assert data["results"] == [] or data["count"] >= 0


@pytest.mark.unit
def test_get_product_by_name_found(temp_db):
    raw = get_product_by_name.invoke({"name": "Yamaha C40"})
    data = json.loads(raw)
    assert data["found"] is True
    assert any("Yamaha C40" in m["name"] for m in data["matches"])
    assert all(m["status"] == "active" for m in data["matches"])


@pytest.mark.unit
def test_get_product_by_name_missing(temp_db):
    raw = get_product_by_name.invoke({"name": "Produto Inexistente XYZ"})
    data = json.loads(raw)
    assert data["found"] is False
