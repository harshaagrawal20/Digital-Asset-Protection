import sqlite3, uuid
from datetime import datetime, timezone
from db_setup import get_conn, init_db
from fingerprint import generate_dna

def register_asset(image_path: str, name: str, owner_org: str, asset_id: str = None) -> dict:
    init_db()
    asset_id = asset_id or f"ASSET_{uuid.uuid4().hex[:8].upper()}"
    registered_at = datetime.now(timezone.utc).isoformat()

    dna = generate_dna(image_path, name, owner_org, registered_at)

    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO asset_registry
              (asset_id, name, owner_org, phash, histogram_sig, metadata_sha, dna_combined, registered_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (asset_id, name, owner_org, dna["phash"], dna["histogram_sig"],
              dna["metadata_sha"], dna["dna_combined"], registered_at))
        conn.commit()
        print(f"[REGISTERED] {asset_id} — {name}")
    finally:
        conn.close()

    return {"asset_id": asset_id, "name": name, "owner_org": owner_org,
            "dna_combined": dna["dna_combined"], "registered_at": registered_at}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python register_asset.py <image_path> <name> <owner_org>")
        sys.exit(1)
    result = register_asset(sys.argv[1], sys.argv[2], sys.argv[3])
    print(result)
