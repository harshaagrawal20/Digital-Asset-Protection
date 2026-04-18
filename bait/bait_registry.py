"""
bait_registry.py — Register bait assets in assets.db bait_log table.
"""
import json
from datetime import datetime, timezone
from db_schema import get_connection


def register_bait(bait_id: str, source_asset: str, seeded_to: str) -> dict:
    """
    Insert a new bait record. seeded_at = now (UTC ISO).
    Returns the inserted row as a dict.
    """
    seeded_at = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO bait_log
           (bait_id, source_asset, seeded_to, seeded_at, detected_at, detected_in, spread_log)
           VALUES (?, ?, ?, ?, NULL, NULL, '[]')""",
        (bait_id, source_asset, seeded_to, seeded_at),
    )
    conn.commit()
    conn.close()
    return {"bait_id": bait_id, "source_asset": source_asset,
            "seeded_to": seeded_to, "seeded_at": seeded_at}


def mark_detected(bait_id: str, detected_in: str) -> bool:
    """
    Set detected_at + detected_in for first detection.
    Returns True if row updated, False if bait_id not found.
    """
    detected_at = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cur = conn.execute(
        "SELECT detected_at FROM bait_log WHERE bait_id = ?", (bait_id,)
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    if row["detected_at"] is None:
        conn.execute(
            "UPDATE bait_log SET detected_at = ?, detected_in = ? WHERE bait_id = ?",
            (detected_at, detected_in, bait_id),
        )
    conn.commit()
    conn.close()
    return True


def append_spread(bait_id: str, channel: str) -> bool:
    """
    Add a new sighting to spread_log JSON array.
    """
    conn = get_connection()
    cur = conn.execute("SELECT spread_log FROM bait_log WHERE bait_id = ?", (bait_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    try:
        log = json.loads(row["spread_log"] or "[]")
    except json.JSONDecodeError:
        log = []
    log.append({"channel": channel, "seen_at": datetime.now(timezone.utc).isoformat()})
    conn.execute(
        "UPDATE bait_log SET spread_log = ? WHERE bait_id = ?",
        (json.dumps(log), bait_id),
    )
    conn.commit()
    conn.close()
    return True
