"""
main.py — CLI for Person A's module.

Commands:
  python main.py register <image> <name> <owner>
  python main.py distribute <asset_id> <recipient> [event_type] [notes]
  python main.py verify <suspect_image>
  python main.py trail <asset_id>
  python main.py evidence <asset_id>
"""
import sys, json
from db_setup import init_db

def cmd_register(args):
    if len(args) < 3:
        print("Usage: register <image_path> <name> <owner_org>"); return
    from register_asset import register_asset
    r = register_asset(args[0], args[1], args[2])
    print(json.dumps({k: v for k, v in r.items() if k != "dna_combined"}, indent=2))

def cmd_distribute(args):
    if len(args) < 2:
        print("Usage: distribute <asset_id> <recipient> [event_type] [notes]"); return
    from ledger import log_distribution
    event = args[2] if len(args) > 2 else "licensed"
    notes = args[3] if len(args) > 3 else ""
    r = log_distribution(args[0], args[1], event, notes)
    print(json.dumps(r, indent=2))

def cmd_verify(args):
    if len(args) < 1:
        print("Usage: verify <suspect_image_path>"); return
    from verify_asset import verify_image
    r = verify_image(args[0])
    trail = r.pop("custody_trail", [])
    print(json.dumps(r, indent=2))
    if trail:
        print("\nCustody trail:")
        for e in trail:
            status = "VIOLATED" if e["event_type"] == "violated" else e["event_type"].upper()
            print(f"  [{status}] {e['timestamp']} → {e['recipient']}")

def cmd_trail(args):
    if len(args) < 1:
        print("Usage: trail <asset_id>"); return
    from ledger import get_custody_trail, verify_ledger_entry
    trail = get_custody_trail(args[0])
    if not trail:
        print("No entries found."); return
    for e in trail:
        valid = verify_ledger_entry(e)
        tag = "✓" if valid else "✗ TAMPERED"
        print(f"  [{e['entry_id']}] {tag} | {e['event_type'].upper()} | {e['timestamp']} | {e['recipient']}")

def cmd_evidence(args):
    if len(args) < 1:
        print("Usage: evidence <asset_id>"); return
    from evidence_export import export_evidence
    export_evidence(args[0])

COMMANDS = {
    "register": cmd_register,
    "distribute": cmd_distribute,
    "verify": cmd_verify,
    "trail": cmd_trail,
    "evidence": cmd_evidence,
}

if __name__ == "__main__":
    init_db()
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Commands: register | distribute | verify | trail | evidence")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
