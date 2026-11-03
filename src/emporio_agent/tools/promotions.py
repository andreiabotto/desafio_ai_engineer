"""Tools de promoções ativas."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from emporio_agent.tools.db import connect


@tool
def get_active_promotions(product_id: Optional[int] = None) -> str:
    """Lista promoções ativas (is_active=1) em produtos active. Opcionalmente filtra por product_id.

    Quando há mais de uma promo no mesmo produto, devolve só a de maior desconto.
    Nunca considere promoções inativas como vigentes.
    PIX 5% NÃO é cumulativo com preço promocional (ver políticas).
    """
    sql = """
        SELECT pr.promotion_id, pr.product_id, pr.discount_percent, pr.description,
               pr.is_active, p.name AS product_name, p.price_brl, p.status, p.stock_quantity
        FROM promotions pr
        JOIN products p ON p.product_id = pr.product_id
        WHERE pr.is_active = 1 AND p.status = 'active'
    """
    params: list = []
    if product_id is not None:
        sql += " AND pr.product_id = ?"
        params.append(product_id)
    sql += " ORDER BY pr.discount_percent DESC LIMIT 50"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    best_by_product: dict[int, dict] = {}
    for r in rows:
        pid = int(r["product_id"])
        if pid in best_by_product:
            continue
        best_by_product[pid] = {
            "promotion_id": r["promotion_id"],
            "product_id": pid,
            "product_name": r["product_name"],
            "price_brl": r["price_brl"],
            "stock_quantity": r["stock_quantity"],
            "discount_percent": r["discount_percent"],
            "description": r["description"],
            "promo_price_brl": round(
                float(r["price_brl"]) * (1 - float(r["discount_percent"]) / 100), 2
            ),
            "pix_stackable": False,
            "note": "Desconto PIX (5%) não é cumulativo com preço promocional.",
        }

    results = list(best_by_product.values())
    results.sort(key=lambda x: float(x["discount_percent"]), reverse=True)

    if not results:
        return json.dumps(
            {
                "count": 0,
                "results": [],
                "message": "Não há promoções ativas no momento para esses critérios.",
                "pix_stackable": False,
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "count": len(results),
            "results": results,
            "pix_stackable": False,
            "message": "PIX 5% não cumulativo com promoções ativas.",
        },
        ensure_ascii=False,
    )
