"""
spread_tracker.py — Tracks further sightings of a detected bait asset.
Reads from bait_log.spread_log (JSON array) and builds a propagation chain.
"""
import json, logging
from bait_registry import append_spread
from db_schema import get_connection

log = logging.getLogger(__name__)


def log_spread_sighting(bait_id: str, channel: str) -> bool:
    """Append a new channel sighting to the spread_log for bait_id."""
    ok = append_spread(bait_id, channel)
    if ok:
        log.info(f"Spread sighting logged: {bait_id} → {channel}")
    return ok


def get_propagation_chain(bait_id: str) -> list[dict]:
    """
    Return full propagation chain for bait_id.
    Each dict: {channel, seen_at}
    """
    conn = get_connection()
    cur = conn.execute(
        "SELECT seeded_to, seeded_at, detected_in, detected_at, spread_log FROM bait_log WHERE bait_id = ?",
        (bait_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return []

    chain = [{"channel": row["seeded_to"], "seen_at": row["seeded_at"], "event": "seeded"}]

    if row["detected_in"] and row["detected_at"]:
        chain.append({"channel": row["detected_in"], "seen_at": row["detected_at"], "event": "first_detection"})

    try:
        spread = json.loads(row["spread_log"] or "[]")
    except json.JSONDecodeError:
        spread = []
    for s in spread:
        chain.append({"channel": s.get("channel"), "seen_at": s.get("seen_at"), "event": "spread"})

    return sorted(chain, key=lambda x: x.get("seen_at") or "")
