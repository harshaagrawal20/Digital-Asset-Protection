"""
bait_api.py — Person C's API (locked Day 1 signatures).
  - get_bait_list()
  - get_leak_trail(bait_id)
"""
import json
from datetime import datetime
from db_schema import get_connection


def get_bait_list() -> list[dict]:
    """Return all bait entries ordered by seeded_at DESC."""
    conn = get_connection()
    cur = conn.execute("SELECT * FROM bait_log ORDER BY seeded_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_leak_trail(bait_id: str) -> dict | None:
    """
    Return full detection + propagation trail for bait_id.
    Keys: bait_id, source_asset, seeded_to, seeded_at,
          detected_at, detected_in, spread_log (list),
          status ('detected'|'pending'), time_to_detection_minutes (float|None)
    """
    conn = get_connection()
    cur = conn.execute("SELECT * FROM bait_log WHERE bait_id = ?", (bait_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None

    result = dict(row)
    try:
        result["spread_log"] = json.loads(result["spread_log"]) if result["spread_log"] else []
    except (json.JSONDecodeError, TypeError):
        result["spread_log"] = []

    if result["detected_at"]:
        result["status"] = "detected"
        seeded = datetime.fromisoformat(result["seeded_at"])
        detected = datetime.fromisoformat(result["detected_at"])
        result["time_to_detection_minutes"] = round((detected - seeded).total_seconds() / 60, 1)
    else:
        result["status"] = "pending"
        result["time_to_detection_minutes"] = None

    return result
