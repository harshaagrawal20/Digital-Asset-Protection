"""
main.py — Person B CLI
Usage:
  python main.py seed <image_path> <channel> [bait_id]
  python main.py detect <image_path> <channel>
  python main.py list
  python main.py trail <bait_id>
  python main.py initdb
"""
import sys
from db_schema import init_db
from bait_generator import generate_bait, extract_bait_id
from bait_registry import register_bait, mark_detected
from bait_api import get_bait_list, get_leak_trail
from spread_tracker import get_propagation_chain
import json


def cmd_seed(image_path, channel, bait_id=None):
    result = generate_bait(image_path, bait_id)
    bait_id = result["bait_id"]
    register_bait(bait_id, image_path, channel)
    print(f"✓ Bait generated: {bait_id}")
    print(f"  Saved to     : {result['bait_path']}")
    print(f"  Seeded to    : {channel}")


def cmd_detect(image_path, channel):
    bait_id = extract_bait_id(image_path)
    if not bait_id:
        print("No bait ID found in image.")
        return
    print(f"Bait ID found: {bait_id}")
    updated = mark_detected(bait_id, channel)
    if updated:
        print(f"✓ First detection logged — channel: {channel}")
    else:
        print(f"Spread sighting logged — channel: {channel}")
        from bait_registry import append_spread
        append_spread(bait_id, channel)


def cmd_list():
    baits = get_bait_list()
    if not baits:
        print("No bait entries found.")
        return
    for b in baits:
        status = "DETECTED" if b["detected_at"] else "PENDING"
        print(f"  [{status}] {b['bait_id']} → seeded to {b['seeded_to']} at {b['seeded_at']}")


def cmd_trail(bait_id):
    trail = get_leak_trail(bait_id)
    if not trail:
        print(f"No record found for {bait_id}")
        return
    print(json.dumps(trail, indent=2))
    chain = get_propagation_chain(bait_id)
    print("\nPropagation chain:")
    for step in chain:
        print(f"  [{step['event'].upper()}] {step['channel']} at {step['seen_at']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]
    if cmd == "initdb":
        init_db(); print("DB initialized.")
    elif cmd == "seed" and len(args) >= 3:
        cmd_seed(args[1], args[2], args[3] if len(args) > 3 else None)
    elif cmd == "detect" and len(args) >= 3:
        cmd_detect(args[1], args[2])
    elif cmd == "list":
        cmd_list()
    elif cmd == "trail" and len(args) >= 2:
        cmd_trail(args[1])
    else:
        print(__doc__)
