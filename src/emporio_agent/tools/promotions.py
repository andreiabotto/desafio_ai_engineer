"""Tools de promoções ativas."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from emporio_agent.tools.db import connect


@tool
def get_active_promotions(product_id: Optional[int] = None) -> str:
    """Lista promoções ativas (is_active=1). Opcionalmente filtra por product_id.

    Nunca considere promoções inativas como vigentes.
    """
    sql = """
        SELECT pr.promotion_id, pr.product_id, pr.discount_percent, pr.description,
               pr.is_active, p.name AS product_name, p.price_brl
        FROM promotions pr
        JOIN products p ON p.product_id = pr.product_id
        WHERE pr.is_active = 1
    """
    params: list = []
    if product_id is not None:
        sql += " AND pr.product_id = ?"
        params.append(product_id)
    sql += " ORDER BY pr.discount_percent DESC"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    results = [
        {
            "promotion_id": r["promotion_id"],
            "product_id": r["product_id"],
            "product_name": r["product_name"],
            "price_brl": r["price_brl"],
            "discount_percent": r["discount_percent"],
            "description": r["description"],
            "promo_price_brl": round(float(r["price_brl"]) * (1 - float(r["discount_percent"]) / 100), 2),
        }
        for r in rows
    ]

    if not results:
        return json.dumps(
            {
                "count": 0,
                "results": [],
                "message": "Não há promoções ativas no momento para esses critérios.",
            },
            ensure_ascii=False,
        )

    return json.dumps({"count": len(results), "results": results}, ensure_ascii=False)