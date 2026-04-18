import sqlite3
from datetime import datetime, timezone
from db_setup import get_conn
from fingerprint import generate_dna, compare_dna
from ledger import get_custody_trail, log_distribution

def verify_image(image_path: str, threshold: int = 12) -> dict:
    """
    Compare image against all registered assets.
    Returns best match + full custody trail if found.
    """
    dna = generate_dna(image_path, "_verify_", "_verify_", datetime.now(timezone.utc).isoformat())
    suspect_dna = dna["dna_combined"]

    conn = get_conn()
    rows = conn.execute("SELECT asset_id, name, owner_org, dna_combined FROM asset_registry").fetchall()
    conn.close()

    best = None
    best_dist = 9999

    for asset_id, name, owner_org, registered_dna in rows:
        result = compare_dna(registered_dna, suspect_dna, threshold)
        if result["match"] and result["hamming_distance"] < best_dist:
            best_dist = result["hamming_distance"]
            best = {
                "asset_id": asset_id,
                "name": name,
                "owner_org": owner_org,
                "hamming_distance": best_dist,
                "match": True
            }

    if not best:
        print("[VERIFY] No match found — asset not in registry or too different.")
        return {"match": False, "asset_id": None, "custody_trail": []}

    # Log the violation event in the ledger
    log_distribution(best["asset_id"], "UNKNOWN/UNAUTHORIZED", "violated",
                     f"Detected copy at path: {image_path} | Hamming: {best_dist}")

    trail = get_custody_trail(best["asset_id"])
    print(f"[VERIFY] MATCH — {best['name']} (dist={best_dist}) | Trail: {len(trail)} entries")
    return {**best, "custody_trail": trail}

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: python verify_asset.py <suspect_image_path>")
        sys.exit(1)
    result = verify_image(sys.argv[1])
    trail = result.pop("custody_trail", [])
    print(json.dumps(result, indent=2))
    if trail:
        print("\n--- Custody Trail ---")
        for e in trail:
            print(f"  [{e['event_type'].upper()}] {e['timestamp']} → {e['recipient']}")
