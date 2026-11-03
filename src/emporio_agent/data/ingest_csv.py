"""Ingestão dos CSVs operacionais para SQLite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

from emporio_agent.config import CSV_FILES, DB_PATH, ensure_runtime_dirs
from emporio_agent.textnorm import digits_only, strip_accents


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    ensure_runtime_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def _csv_fingerprint(csv_files: dict[str, Path]) -> str:
    h = hashlib.sha256()
    for key in sorted(csv_files):
        path = csv_files[key]
        h.update(key.encode())
        h.update(str(path.stat().st_mtime_ns).encode())
        h.update(str(path.stat().st_size).encode())
    return h.hexdigest()[:16]


def ingest_csvs(db_path: Path | None = None, csv_files: dict[str, Path] | None = None) -> Path:
    """Carrega CSVs no SQLite com tipagem, índices e colunas de busca."""
    path = Path(db_path) if db_path else DB_PATH
    files = csv_files or CSV_FILES
    ensure_runtime_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)

    categories = _read_csv(files["categories"])
    customers = _read_csv(files["customers"])
    products = _read_csv(files["products"])
    promotions = _read_csv(files["promotions"])
    orders = _read_csv(files["orders"])
    order_items = _read_csv(files["order_items"])

    products["price_brl"] = pd.to_numeric(products["price_brl"], errors="coerce")
    products["stock_quantity"] = (
        pd.to_numeric(products["stock_quantity"], errors="coerce").fillna(0).astype(int)
    )
    products["category_id"] = pd.to_numeric(products["category_id"], errors="coerce").astype("Int64")
    products["status"] = products["status"].astype(str).str.strip().str.lower()
    products["name_search"] = products["name"].astype(str).map(strip_accents).str.lower()
    products["description_search"] = (
        products["description"].fillna("").astype(str).map(strip_accents).str.lower()
    )

    categories["name_search"] = categories["name"].astype(str).map(strip_accents).str.lower()

    customers["phone_digits"] = customers["phone"].fillna("").astype(str).map(digits_only)

    promotions["discount_percent"] = pd.to_numeric(
        promotions["discount_percent"], errors="coerce"
    ).fillna(0)
    promotions["is_active"] = (
        pd.to_numeric(promotions["is_active"], errors="coerce").fillna(0).astype(int)
    )

    orders["total_brl"] = pd.to_numeric(orders["total_brl"], errors="coerce")
    orders["status"] = orders["status"].astype(str).str.strip().str.lower()
    orders["tracking_code"] = orders["tracking_code"].fillna("").astype(str)
    orders["notes"] = orders["notes"].fillna("").astype(str)

    order_items["quantity"] = (
        pd.to_numeric(order_items["quantity"], errors="coerce").fillna(1).astype(int)
    )
    # Snapshot do preço de catálogo no momento da ingestão (CSV não traz unit_price histórico)
    price_map = products.set_index("product_id")["price_brl"].to_dict()
    order_items["unit_price_brl"] = order_items["product_id"].map(price_map)

    fingerprint = _csv_fingerprint(files)

    with get_connection(path) as conn:
        categories.to_sql("categories", conn, if_exists="replace", index=False)
        customers.to_sql("customers", conn, if_exists="replace", index=False)
        products.to_sql("products", conn, if_exists="replace", index=False)
        promotions.to_sql("promotions", conn, if_exists="replace", index=False)
        orders.to_sql("orders", conn, if_exists="replace", index=False)
        order_items.to_sql("order_items", conn, if_exists="replace", index=False)

        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);
            CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
            CREATE INDEX IF NOT EXISTS idx_products_name_search ON products(name_search);
            CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
            CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
            CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
            CREATE INDEX IF NOT EXISTS idx_orders_tracking ON orders(tracking_code);
            CREATE INDEX IF NOT EXISTS idx_customers_customer_id ON customers(customer_id);
            CREATE INDEX IF NOT EXISTS idx_customers_phone_digits ON customers(phone_digits);
            CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
            CREATE INDEX IF NOT EXISTS idx_promotions_product_id ON promotions(product_id);
            CREATE INDEX IF NOT EXISTS idx_promotions_active ON promotions(is_active);
            """
        )
        meta = path.parent / f"{path.stem}.meta.json"
        meta.write_text(
            json.dumps({"csv_fingerprint": fingerprint}, ensure_ascii=False),
            encoding="utf-8",
        )
        conn.commit()

    return path


def db_ready(db_path: Path | None = None, csv_files: dict[str, Path] | None = None) -> bool:
    path = Path(db_path) if db_path else DB_PATH
    files = csv_files or CSV_FILES
    if not path.exists():
        return False
    with get_connection(path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(products)").fetchall()
        }
        item_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(order_items)").fetchall()
        }
    expected = {"categories", "customers", "products", "promotions", "orders", "order_items"}
    if not expected.issubset(tables):
        return False
    if "name_search" not in cols or "unit_price_brl" not in item_cols:
        return False
    meta = path.parent / f"{path.stem}.meta.json"
    if not meta.exists():
        return False
    try:
        stored = json.loads(meta.read_text(encoding="utf-8")).get("csv_fingerprint")
    except (json.JSONDecodeError, OSError):
        return False
    return stored == _csv_fingerprint(files)


if __name__ == "__main__":
    out = ingest_csvs()
    print(f"SQLite pronto em {out}")
