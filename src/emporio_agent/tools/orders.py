"""Tools de pedidos e rastreamento."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from emporio_agent.tools.db import connect
from emporio_agent.textnorm import normalize_phone_digits


def _mask_name(name: str | None) -> str:
    raw = (name or "").strip()
    if not raw:
        return ""
    parts = raw.split()
    if len(parts) == 1:
        return parts[0][:1] + "***"
    return f"{parts[0]} {parts[-1][:1]}***"


@tool
def get_order_status(
    order_id: Optional[int] = None,
    tracking_code: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> str:
    """Consulta status de pedido por order_id, código de rastreio, e-mail ou telefone do cliente.

    Informe ao menos um identificador. Se informar vários, TODOS precisam bater (AND).
    Não invente status — use apenas o retorno desta tool.
    E-mail e telefone NÃO são devolvidos no JSON (LGPD / minimização).
    """
    if not any([order_id is not None, tracking_code, email, phone]):
        return json.dumps(
            {
                "found": False,
                "message": "Informe order_id, tracking_code, email ou telefone para localizar o pedido.",
            },
            ensure_ascii=False,
        )

    phone_digits = normalize_phone_digits(phone or "")
    if phone and len(phone_digits) < 8:
        return json.dumps(
            {
                "found": False,
                "message": "Telefone inválido ou incompleto. Informe DDD + número (ao menos 8 dígitos).",
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
        clauses.append("c.phone_digits = ?")
        params.append(phone_digits)

    where = " AND ".join(clauses)
    sql = f"""
        SELECT o.order_id, o.order_date, o.status, o.total_brl, o.payment_method,
               o.tracking_code, o.estimated_delivery, o.notes,
               c.name AS customer_name, c.city
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE {where}
        ORDER BY o.order_date DESC
        LIMIT 5
    """

    strong_id = order_id is not None or bool(tracking_code)

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
                SELECT oi.quantity, oi.unit_price_brl, p.name
                FROM order_items oi
                JOIN products p ON p.product_id = oi.product_id
                WHERE oi.order_id = ?
                """,
                [order["order_id"]],
            ).fetchall()
            entry = {
                "order_id": order["order_id"],
                "order_date": order["order_date"],
                "status": order["status"],
                "total_brl": order["total_brl"],
                "payment_method": order["payment_method"],
                "tracking_code": order["tracking_code"],
                "estimated_delivery": order["estimated_delivery"],
                "city": order["city"],
                "items": [
                    {
                        "name": i["name"],
                        "quantity": i["quantity"],
                        "unit_price_brl": i["unit_price_brl"],
                    }
                    for i in items
                ],
            }
            if strong_id:
                entry["customer_name"] = order["customer_name"]
                notes = (order["notes"] or "").strip()
                if notes:
                    entry["notes"] = notes
            else:
                entry["customer_name"] = _mask_name(order["customer_name"])
            results.append(entry)

    return json.dumps(
        {
            "found": True,
            "orders": results,
            "privacy_note": "email e telefone nunca são retornados por esta tool.",
        },
        ensure_ascii=False,
    )
