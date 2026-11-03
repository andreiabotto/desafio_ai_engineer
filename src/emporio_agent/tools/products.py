"""Tools de catálogo de produtos."""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from emporio_agent.tools.db import connect
from emporio_agent.textnorm import like_pattern, looks_like_accessory_query, strip_accents


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


def _category_hint(cat: str) -> str:
    low = cat.lower()
    if "eletr" in low:
        return " Dica: a categoria no catálogo é 'Guitarras' (não 'Guitarras Elétricas')."
    if "sopro" in low or "sax" in low or "flauta" in low:
        return " Dica: tente 'Instrumentos de Sopro'."
    if "ukule" in low or "ukele" in low:
        return " Dica: a categoria no catálogo é 'Ukuleles'."
    if "orquestr" in low or "violino" in low or "cello" in low:
        return " Dica: tente 'Cordas Orquestrais'."
    return ""


@tool
def search_products(
    query: Optional[str] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
) -> str:
    """Busca produtos no catálogo por nome/descrição e/ou categoria, com preço máximo opcional.

    Informe ao menos um de: query, category ou max_price.
    Use in_stock=true para listar só itens com estoque > 0 (útil para alternativas).
    Categorias reais incluem: Guitarras, Baixos, Violões, Ukuleles, Teclados e Pianos,
    Baterias e Percussão, Cordas Orquestrais, Instrumentos de Sopro (Madeiras/Metais).
    Exemplos: query="violão" + max_price=1000; category="Guitarras".
    """
    q = (query or "").strip()
    cat = (category or "").strip()
    if not q and not cat and max_price is None:
        return json.dumps(
            {
                "results": [],
                "message": "Informe query, category ou max_price para buscar produtos.",
            },
            ensure_ascii=False,
        )

    if q and looks_like_accessory_query(q) and not cat:
        return json.dumps(
            {
                "results": [],
                "out_of_scope": True,
                "message": (
                    "A Empório da Música não vende acessórios (cordas avulsas, palhetas, "
                    "cabos, cases, pedais, amplificadores). Escopo: apenas instrumentos."
                ),
            },
            ensure_ascii=False,
        )

    sql = """
        SELECT p.product_id, p.name, p.price_brl, p.stock_quantity, p.status,
               p.description, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE p.status = 'active'
    """
    params: list = []

    if q:
        pattern = like_pattern(q)
        sql += """
          AND (
            LOWER(p.name_search) LIKE LOWER(?) ESCAPE '\\'
            OR LOWER(IFNULL(p.description_search, '')) LIKE LOWER(?) ESCAPE '\\'
            OR LOWER(IFNULL(c.name_search, c.name)) LIKE LOWER(?) ESCAPE '\\'
          )
        """
        params.extend([pattern, pattern, pattern])

    if max_price is not None:
        sql += " AND p.price_brl <= ?"
        params.append(max_price)
    if cat:
        sql += " AND LOWER(IFNULL(c.name_search, c.name)) LIKE LOWER(?) ESCAPE '\\'"
        params.append(like_pattern(cat))
    if in_stock is True:
        sql += " AND p.stock_quantity > 0"
    elif in_stock is False:
        sql += " AND p.stock_quantity <= 0"

    sql += " ORDER BY p.price_brl ASC LIMIT 16"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    truncated = len(rows) > 15
    rows = rows[:15]

    if not rows:
        hint = _category_hint(cat or q)
        return json.dumps(
            {
                "results": [],
                "message": f"Nenhum produto encontrado com esses critérios.{hint}",
            },
            ensure_ascii=False,
        )

    results = [_row_to_product(r) for r in rows]
    payload: dict = {"count": len(results), "results": results}
    if truncated:
        payload["truncated"] = True
        payload["message"] = "Há mais resultados; refine query/categoria/preço se precisar."
    return json.dumps(payload, ensure_ascii=False)


@tool
def get_product_by_name(name: str) -> str:
    """Busca um produto específico pelo nome (match parcial, case-insensitive).

    Use para preço, estoque e detalhes de um modelo (ex.: Takamine GD20).
    Prioriza produtos active; discontinued/coming_soon só aparecem se não houver ativo.
    """
    pattern = like_pattern(name)
    exact = strip_accents(name).strip().lower()
    sql = """
        SELECT p.product_id, p.name, p.price_brl, p.stock_quantity, p.status,
               p.description, p.specs, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE LOWER(p.name_search) LIKE LOWER(?) ESCAPE '\\'
        ORDER BY
          CASE WHEN p.status = 'active' THEN 0 ELSE 1 END,
          CASE WHEN LOWER(p.name_search) = LOWER(?) THEN 0 ELSE 1 END,
          LENGTH(p.name) ASC
        LIMIT 5
    """
    with connect() as conn:
        rows = conn.execute(sql, [pattern, exact]).fetchall()

    if not rows:
        return json.dumps(
            {"found": False, "message": f"Produto '{name}' não encontrado no catálogo."},
            ensure_ascii=False,
        )

    active = [r for r in rows if r["status"] == "active"]
    chosen = active or list(rows)

    products = []
    for row in chosen:
        item = _row_to_product(row)
        item["specs"] = row["specs"]
        products.append(item)

    return json.dumps({"found": True, "matches": products}, ensure_ascii=False)
