"""Tools de catálogo de produtos."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from emporio_agent.tools.db import connect


def _row_to_product(row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "price_brl": row["price_brl"],
        "category": row["category_name"],
        "stock_quantity": row["stock_quantity"],
        "status": row["status"],
        "description": row["description"],
    }


@tool
def search_products(
    query: str,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
) -> str:
    """Busca produtos no catálogo por nome/descrição, com filtros opcionais de preço máximo e categoria.

    Use para listar opções disponíveis (ex.: violões até R$ 1000).
    """
    sql = """
        SELECT p.product_id, p.name, p.price_brl, p.stock_quantity, p.status,
               p.description, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE p.status = 'active'
          AND (
            LOWER(p.name) LIKE LOWER(?)
            OR LOWER(p.description) LIKE LOWER(?)
            OR LOWER(IFNULL(c.name, '')) LIKE LOWER(?)
          )
    """
    params: list = [f"%{query}%", f"%{query}%", f"%{query}%"]

    if max_price is not None:
        sql += " AND p.price_brl <= ?"
        params.append(max_price)
    if category:
        sql += " AND LOWER(c.name) LIKE LOWER(?)"
        params.append(f"%{category}%")

    sql += " ORDER BY p.price_brl ASC LIMIT 15"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    if not rows:
        return json.dumps(
            {"results": [], "message": "Nenhum produto encontrado com esses critérios."},
            ensure_ascii=False,
        )

    results = [_row_to_product(r) for r in rows]
    return json.dumps({"count": len(results), "results": results}, ensure_ascii=False)


@tool
def get_product_by_name(name: str) -> str:
    """Busca um produto específico pelo nome (match parcial, case-insensitive).

    Use para preço, estoque e detalhes de um modelo (ex.: Takamine GD20).
    """
    sql = """
        SELECT p.product_id, p.name, p.price_brl, p.stock_quantity, p.status,
               p.description, p.specs, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE LOWER(p.name) LIKE LOWER(?)
        ORDER BY
          CASE WHEN LOWER(p.name) = LOWER(?) THEN 0 ELSE 1 END,
          LENGTH(p.name) ASC
        LIMIT 5
    """
    with connect() as conn:
        rows = conn.execute(sql, [f"%{name}%", name]).fetchall()

    if not rows:
        return json.dumps(
            {"found": False, "message": f"Produto '{name}' não encontrado no catálogo."},
            ensure_ascii=False,
        )

    products = []
    for row in rows:
        item = _row_to_product(row)
        item["specs"] = row["specs"]
        products.append(item)

    return json.dumps({"found": True, "matches": products}, ensure_ascii=False)