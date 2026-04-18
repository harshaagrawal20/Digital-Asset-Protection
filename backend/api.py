"""
api.py — Clean interface for Person C's dashboard.
Import this file only. Don't import other modules directly.
"""
import sqlite3
from db_setup import get_conn, init_db
from ledger import get_custody_trail
from verify_asset import verify_image
from evidence_export import export_evidence

def get_asset_list() -> list:
    """Returns all registered assets as a list of dicts."""
    init_db()
    conn = get_conn()
    rows = conn.execute("""
        SELECT asset_id, name, owner_org, phash, registered_at FROM asset_registry ORDER BY registered_at DESC
    """).fetchall()
    conn.close()
    keys = ["asset_id","name","owner_org","phash","registered_at"]
    return [dict(zip(keys, r)) for r in rows]

def get_custody_trail_api(asset_id: str) -> list:
    """Returns full custody trail for one asset."""
    return get_custody_trail(asset_id)

def verify_image_api(image_path: str) -> dict:
    """Verify a suspected image. Returns match result + custody trail."""
    return verify_image(image_path)

def export_evidence_api(asset_id: str, output_path: str = None) -> dict:
    """Generate JSON evidence report for an asset."""
    return export_evidence(asset_id, output_path)
