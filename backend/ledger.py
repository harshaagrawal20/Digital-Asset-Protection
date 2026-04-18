import hmac, hashlib, os, json
from datetime import datetime, timezone
from db_setup import get_conn

SIGNING_KEY = os.environ.get("SIGNING_KEY", "change_this_in_production_32bytes!")

def _sign(asset_id, event_type, recipient, notes, timestamp) -> str:
    payload = f"{asset_id}|{event_type}|{recipient}|{notes}|{timestamp}"
    return hmac.new(SIGNING_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()

def log_distribution(asset_id: str, recipient: str, event_type: str = "licensed", notes: str = "") -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    sig = _sign(asset_id, event_type, recipient, notes, timestamp)

    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO custody_ledger (asset_id, event_type, recipient, notes, timestamp, hmac_sig)
            VALUES (?,?,?,?,?,?)
        """, (asset_id, event_type, recipient, notes, timestamp, sig))
        conn.commit()
        print(f"[LEDGER] {event_type.upper()} → {recipient} for {asset_id}")
    finally:
        conn.close()

    return {"asset_id": asset_id, "event_type": event_type,
            "recipient": recipient, "timestamp": timestamp, "hmac_sig": sig}

def get_custody_trail(asset_id: str) -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT entry_id, asset_id, event_type, recipient, notes, timestamp, hmac_sig
        FROM custody_ledger WHERE asset_id = ? ORDER BY entry_id ASC
    """, (asset_id,)).fetchall()
    conn.close()
    keys = ["entry_id","asset_id","event_type","recipient","notes","timestamp","hmac_sig"]
    return [dict(zip(keys, r)) for r in rows]

def verify_ledger_entry(entry: dict) -> bool:
    expected = _sign(entry["asset_id"], entry["event_type"],
                     entry["recipient"], entry["notes"] or "", entry["timestamp"])
    return hmac.compare_digest(expected, entry["hmac_sig"])

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python ledger.py <asset_id> <recipient> [event_type] [notes]")
        sys.exit(1)
    event_type = sys.argv[3] if len(sys.argv) > 3 else "licensed"
    notes = sys.argv[4] if len(sys.argv) > 4 else ""
    print(log_distribution(sys.argv[1], sys.argv[2], event_type, notes))
