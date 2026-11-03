"""Tools de pedidos e rastreamento."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from emporio_agent.tools.db import connect


@tool
def get_order_status(
    order_id: Optional[int] = None,
    tracking_code: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> str:
    """Consulta status de pedido por order_id, código de rastreio, e-mail ou telefone do cliente.

    Informe ao menos um identificador. Não invente status — use apenas o retorno desta tool.
    """
    if not any([order_id, tracking_code, email, phone]):
        return json.dumps(
            {
                "found": False,
                "message": "Informe order_id, tracking_code, email ou telefone para localizar o pedido.",
            },
            ensure_ascii=False,
        )

    clauses = []
    params: list = []
    if order_id is not None:
        clauses.append("o.order_id = ?")
        params.append(order_id)
    if tracking_code:
        clauses.append("UPPER(o.tracking_code) = UPPER(?)")
        params.append(tracking_code.strip())
    if email:
        clauses.append("LOWER(c.email) = LOWER(?)")
        params.append(email.strip())
    if phone:
        digits = "".join(ch for ch in phone if ch.isdigit())
        clauses.append(
            "REPLACE(REPLACE(REPLACE(REPLACE(c.phone, '(', ''), ')', ''), '-', ''), ' ', '') LIKE ?"
        )
        params.append(f"%{digits}%")

    where = " OR ".join(clauses)
    sql = f"""
        SELECT o.order_id, o.order_date, o.status, o.total_brl, o.payment_method,
               o.tracking_code, o.estimated_delivery, o.notes,
               c.name AS customer_name, c.email, c.phone, c.city
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE {where}
        ORDER BY o.order_date DESC
        LIMIT 5
    """

    with connect() as conn:
        orders = conn.execute(sql, params).fetchall()
        if not orders:
            return json.dumps(
                {"found": False, "message": "Nenhum pedido encontrado com os dados informados."},
                ensure_ascii=False,
            )

        results = []
        for order in orders:
            items = conn.execute(
                """
                SELECT oi.quantity, p.name, p.price_brl
                FROM order_items oi
                JOIN products p ON p.product_id = oi.product_id
                WHERE oi.order_id = ?
                """,
                [order["order_id"]],
            ).fetchall()
            results.append(
                {
                    "order_id": order["order_id"],
                    "order_date": order["order_date"],
                    "status": order["status"],
                    "total_brl": order["total_brl"],
                    "payment_method": order["payment_method"],
                    "tracking_code": order["tracking_code"],
                    "estimated_delivery": order["estimated_delivery"],
                    "notes": order["notes"],
                    "customer_name": order["customer_name"],
                    "city": order["city"],
                    "items": [
                        {
                            "name": i["name"],
                            "quantity": i["quantity"],
                            "price_brl": i["price_brl"],
                        }
                        for i in items
                    ],
                }
            )

    return json.dumps({"found": True, "orders": results}, ensure_ascii=False)