"""
Unified Database Seeding Script.
Registers real assets using Person A's fingerprint engine,
seeds bait data, and creates custody events for demo.
"""
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))
sys.path.append(os.path.join(project_root, 'bait'))
os.environ["DB_PATH"] = os.path.join(project_root, 'assets.db')

import sqlite3
import json
import hashlib
import hmac
from datetime import datetime, timedelta

# Initialize schemas from both modules
import db_setup as backend_db
import bait.db_schema as bait_db

print("Initializing Master Database...")
backend_db.init_db()
bait_db.init_db()

# --- Register assets using Person A's REAL fingerprint engine ---
print("Registering assets with real DNA fingerprints...")

from register_asset import register_asset

sport1_path = os.path.join(project_root, 'backend', 'sport1.jpeg')

# Clear existing data for idempotent seeding
db_path = os.environ["DB_PATH"]
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
conn.execute("DELETE FROM custody_ledger")
conn.execute("DELETE FROM bait_log")
conn.execute("DELETE FROM asset_registry")
conn.commit()
conn.close()

# Register sport1.jpeg as ASSET_001 using Person A's real engine
if os.path.exists(sport1_path):
    register_asset(sport1_path, "IPL 2026 Final - Match Highlight Clip",
                   "Board of Control for Cricket in India", "ASSET_001")
    print("[OK] Registered ASSET_001 with real pHash from sport1.jpeg")
else:
    print(f"[WARN] sport1.jpeg not found at {sport1_path}")

# Register suspect.png as ASSET_002
suspect_path = os.path.join(project_root, 'backend', 'suspect.png')
if os.path.exists(suspect_path):
    register_asset(suspect_path, "Premier League Goal Replay - Week 38",
                   "English Premier League", "ASSET_002")
    print("[OK] Registered ASSET_002 with real pHash from suspect.png")

# Register a third asset using sport1.jpeg with different metadata
if os.path.exists(sport1_path):
    register_asset(sport1_path, "NBA Playoffs Dunk Compilation",
                   "National Basketball Association", "ASSET_003")
    print("[OK] Registered ASSET_003 with real pHash")

# --- Custody Ledger using Person A's ledger module ---
print("Creating custody events...")

from ledger import log_distribution

log_distribution("ASSET_001", "Star Sports India", "licensed",
                 "Exclusive broadcast rights for 48 hours")
log_distribution("ASSET_001", "Hotstar Streaming Platform", "distributed",
                 "Digital streaming distribution")
log_distribution("ASSET_001", "Unknown - Telegram Channel @sportleaks", "violated",
                 "Unauthorized upload detected, resized to 480p")
log_distribution("ASSET_002", "Sky Sports UK", "licensed",
                 "Match day highlight package")
log_distribution("ASSET_002", "BBC Sport Online", "distributed",
                 "Web clip rights for 24 hours")
log_distribution("ASSET_003", "ESPN Networks", "licensed",
                 "Full broadcast and digital rights")

print("[OK] Created 6 custody events with valid HMAC signatures")

# --- Bait Log ---
print("Seeding bait data...")

base_time = datetime(2026, 4, 17, 9, 0, 0)

conn = sqlite3.connect(db_path)
baits = [
    {
        "bait_id": "BAIT_001",
        "source_asset": "IPL 2026 Final - Match Highlight Clip",
        "seeded_to": "Telegram @sportleaks",
        "seeded_at": (base_time + timedelta(hours=1)).isoformat(),
        "detected_at": (base_time + timedelta(hours=1, minutes=47)).isoformat(),
        "detected_in": "Telegram @piratedclips",
        "spread_log": json.dumps([
            {
                "channel": "Telegram @piratedclips",
                "time": (base_time + timedelta(hours=1, minutes=47)).isoformat(),
                "type": "first_detection"
            },
            {
                "channel": "Telegram @freesportshd",
                "time": (base_time + timedelta(hours=2, minutes=15)).isoformat(),
                "type": "reshare"
            },
            {
                "channel": "Discord #leaked-content",
                "time": (base_time + timedelta(hours=3, minutes=5)).isoformat(),
                "type": "cross_platform"
            }
        ])
    },
    {
        "bait_id": "BAIT_002",
        "source_asset": "Premier League Goal Replay - Week 38",
        "seeded_to": "Discord #sports-streams",
        "seeded_at": (base_time + timedelta(hours=4)).isoformat(),
        "detected_at": None,
        "detected_in": None,
        "spread_log": json.dumps([])
    },
]

for b in baits:
    conn.execute("""
        INSERT INTO bait_log
        (bait_id, source_asset, seeded_to, seeded_at, detected_at, detected_in, spread_log)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        b["bait_id"], b["source_asset"], b["seeded_to"],
        b["seeded_at"], b["detected_at"], b["detected_in"],
        b["spread_log"]
    ))

conn.commit()
conn.close()
print(f"[OK] Seeded {len(baits)} bait entries")

print("\n=== Integration DB Ready! All features should work end-to-end. ===")
