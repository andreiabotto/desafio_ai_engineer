import sqlite3

import pytest

from emporio_agent.data.ingest_csv import ingest_csvs


@pytest.mark.unit
def test_ingest_csv_row_counts(temp_db):
    with sqlite3.connect(temp_db) as conn:
        counts = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in [
                "categories",
                "customers",
                "products",
                "promotions",
                "orders",
                "order_items",
            ]
        }
    assert counts["categories"] == 9
    assert counts["customers"] == 50
    assert counts["products"] == 65
    assert counts["promotions"] == 25
    assert counts["orders"] == 20
    assert counts["order_items"] == 22


@pytest.mark.unit
def test_known_product_yamaha_c40(temp_db):
    with sqlite3.connect(temp_db) as conn:
        row = conn.execute(
            "SELECT name, price_brl, stock_quantity, status FROM products WHERE product_id = 81"
        ).fetchone()
    assert row is not None
    assert "Yamaha C40" in row[0]
    assert float(row[1]) == pytest.approx(599.9)
    assert int(row[2]) >= 0
    assert row[3] == "active"


@pytest.mark.unit
def test_order_has_tracking(temp_db):
    with sqlite3.connect(temp_db) as conn:
        row = conn.execute(
            "SELECT tracking_code, status FROM orders WHERE order_id = 1"
        ).fetchone()
    assert row is not None
    assert row[0].startswith("BR")
    assert row[1] == "delivered"


@pytest.mark.unit
def test_reingest_idempotent(tmp_path):
    db = tmp_path / "a.db"
    ingest_csvs(db_path=db)
    ingest_csvs(db_path=db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 65


@pytest.mark.unit
def test_ingest_has_search_and_unit_price(temp_db):
    with sqlite3.connect(temp_db) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
        item_cols = {r[1] for r in conn.execute("PRAGMA table_info(order_items)").fetchall()}
        cust_cols = {r[1] for r in conn.execute("PRAGMA table_info(customers)").fetchall()}
    assert "name_search" in cols
    assert "unit_price_brl" in item_cols
    assert "phone_digits" in cust_cols
