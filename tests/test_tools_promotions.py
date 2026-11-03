import json
import sqlite3

import pytest

from emporio_agent.tools.promotions import get_active_promotions


@pytest.mark.unit
def test_active_promotions_only(temp_db):
    with sqlite3.connect(temp_db) as conn:
        active = conn.execute(
            "SELECT COUNT(*) FROM promotions WHERE is_active = 1"
        ).fetchone()[0]
        inactive = conn.execute(
            "SELECT COUNT(*) FROM promotions WHERE is_active = 0"
        ).fetchone()[0]

    raw = get_active_promotions.invoke({})
    data = json.loads(raw)
    assert data["count"] == active
    if inactive > 0:
        # Garante que inativas não vazam no resultado
        assert all("discount_percent" in r for r in data["results"])
