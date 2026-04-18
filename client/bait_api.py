"""
Person B's API -- Mock implementation for Person C's dashboard.
Replace these with real imports from Person B's module on Day 2.

Function signatures locked at Day 1 morning:
  - get_bait_list()
  - get_leak_trail(bait_id)
"""

import json
from db_schema import get_connection


def get_bait_list():
    """
    Return all bait entries from the bait_log table.
    Returns: list of dicts with all bait_log columns.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bait_log ORDER BY seeded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_leak_trail(bait_id: str):
    """
    Return the full detection and propagation trail for a bait asset.
    Returns: dict with keys:
        - bait_id (str)
        - source_asset (str)
        - seeded_to (str)
        - seeded_at (str)
        - detected_at (str or None)
        - detected_in (str or None)
        - spread_log (list of dicts)
        - status (str: 'detected', 'pending', 'undetected')
        - time_to_detection_minutes (float or None)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bait_log WHERE bait_id = ?", (bait_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    result = dict(row)

    # Parse spread_log from JSON string to list
    try:
        result["spread_log"] = json.loads(result["spread_log"]) if result["spread_log"] else []
    except (json.JSONDecodeError, TypeError):
        result["spread_log"] = []

    # Compute status
    if result["detected_at"]:
        result["status"] = "detected"
        # Compute time to detection
        from datetime import datetime
        seeded = datetime.fromisoformat(result["seeded_at"])
        detected = datetime.fromisoformat(result["detected_at"])
        delta = detected - seeded
        result["time_to_detection_minutes"] = round(delta.total_seconds() / 60, 1)
    else:
        result["status"] = "pending"
        result["time_to_detection_minutes"] = None

    return result
