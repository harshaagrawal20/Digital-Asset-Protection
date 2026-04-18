import json, sqlite3
from datetime import datetime, timezone
from db_setup import get_conn
from ledger import get_custody_trail, verify_ledger_entry

def export_evidence(asset_id: str, output_path: str = None) -> dict:
    conn = get_conn()
    row = conn.execute("""
        SELECT asset_id, name, owner_org, phash, dna_combined, registered_at
        FROM asset_registry WHERE asset_id = ?
    """, (asset_id,)).fetchone()
    conn.close()

    if not row:
        print(f"[EVIDENCE] Asset {asset_id} not found.")
        return {}

    trail = get_custody_trail(asset_id)
    tamper_checks = [{"entry_id": e["entry_id"], "valid": verify_ledger_entry(e)} for e in trail]
    violations = [e for e in trail if e["event_type"] == "violated"]

    report = {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "asset": {
            "asset_id": row[0], "name": row[1], "owner_org": row[2],
            "phash": row[3], "dna_combined": row[4][:80] + "...",
            "registered_at": row[5]
        },
        "custody_trail": trail,
        "tamper_verification": tamper_checks,
        "violations_detected": len(violations),
        "violation_events": violations,
        "all_entries_valid": all(t["valid"] for t in tamper_checks)
    }

    path = output_path or f"evidence_{asset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[EVIDENCE] Report saved → {path}")
    print(f"  Asset: {row[1]} | Trail entries: {len(trail)} | Violations: {len(violations)} | Tamper-free: {report['all_entries_valid']}")
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python evidence_export.py <asset_id> [output_path]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    export_evidence(sys.argv[1], out)
