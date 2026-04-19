"""
Integration adapter for Person A's backend module.
Queries the shared database directly for full column data,
and calls Person A's verify_image for real fingerprint comparison.
"""
import sqlite3
import os


def _get_conn():
    """Get connection to the shared database with Row factory."""
    db_path = os.environ.get("DB_PATH", "assets.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_asset_list():
    """Return all registered assets as list of dicts with ALL columns."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM asset_registry ORDER BY registered_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_custody_trail(asset_id: str):
    """Return full custody trail for an asset as list of dicts."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM custody_ledger WHERE asset_id = ? ORDER BY timestamp ASC",
        (asset_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def verify_image(image_path: str):
    """
    Call Person A's real fingerprint engine to verify a suspect image.
    Maps their response format to what the dashboard UI expects.
    """
    if not image_path or not os.path.exists(image_path):
        return {
            "matched": False,
            "asset_id": None,
            "asset_name": None,
            "confidence": 0.0,
            "phash_distance": -1,
            "details": "File not found or invalid path."
        }

    try:
        # Use Person A's real verify_image engine
        from verify_asset import verify_image as backend_verify
        res = backend_verify(image_path)

        if res.get("match"):
            confidence = 1.0 - (res.get("hamming_distance", 0) / 64.0)
            return {
                "matched": True,
                "asset_id": res.get("asset_id"),
                "asset_name": res.get("name"),
                "confidence": round(confidence, 2),
                "phash_distance": res.get("hamming_distance", 0),
                "details": f"Perceptual hash match found. Hamming distance: {res.get('hamming_distance', 0)} "
                           f"(threshold: 12). Asset belongs to {res.get('owner_org', 'Unknown')}."
            }
        else:
            return {
                "matched": False,
                "asset_id": None,
                "asset_name": None,
                "confidence": 0.0,
                "phash_distance": -1,
                "details": "No matching asset found in registry."
            }
    except Exception as e:
        return {
            "matched": False,
            "asset_id": None,
            "asset_name": None,
            "confidence": 0.0,
            "phash_distance": -1,
            "details": f"Verification error: {str(e)}"
        }
