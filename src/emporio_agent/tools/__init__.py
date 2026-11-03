"""Ferramentas expostas ao agente."""

from emporio_agent.tools.datetime_tool import get_current_datetime
from emporio_agent.tools.orders import get_order_status
from emporio_agent.tools.policies import search_policies
from emporio_agent.tools.products import get_product_by_name, search_products
from emporio_agent.tools.promotions import get_active_promotions

ALL_TOOLS = [
    search_products,
    get_product_by_name,
    get_active_promotions,
    get_order_status,
    search_policies,
    get_current_datetime,
]

__all__ = [
    "ALL_TOOLS",
    "search_products",
    "get_product_by_name",
    "get_active_promotions",
    "get_order_status",
    "search_policies",
    "get_current_datetime",
]
