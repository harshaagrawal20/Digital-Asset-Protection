"""
Seed demo data into assets.db for Person C's dashboard development.
Inserts 3 assets, custody events, and 2 bait entries with realistic data.
"""

import sqlite3
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta

from db_schema import get_connection, init_db, DB_PATH

HMAC_SECRET = b"digital_asset_protection_secret_2026"


def compute_hmac(fields: list) -> str:
    """Compute HMAC-SHA256 over a list of field values."""
    message = "|".join(str(f) for f in fields)
    return hmac.new(HMAC_SECRET, message.encode(), hashlib.sha256).hexdigest()


def seed():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data for idempotent seeding
    cursor.execute("DELETE FROM custody_ledger")
    cursor.execute("DELETE FROM bait_log")
    cursor.execute("DELETE FROM asset_registry")

    # ---- Asset Registry ----
    base_time = datetime(2026, 4, 17, 9, 0, 0)

    assets = [
        {
            "asset_id": "ASSET_001",
            "name": "IPL 2026 Final - Match Highlight Clip",
            "owner_org": "Board of Control for Cricket in India",
            "phash": "cf46b130cf9a2639",
            "histogram_sig": "0.164,0.167,0.220,0.362,0.438,0.366,0.315,0.281",
            "registered_at": (base_time).isoformat(),
        },
        {
            "asset_id": "ASSET_002",
            "name": "Premier League Goal Replay - Week 38",
            "owner_org": "English Premier League",
            "phash": "b7d4e3f2a1c8b9d6",
            "histogram_sig": "0.10,0.14,0.11,0.19,0.21,0.08,0.10,0.07",
            "registered_at": (base_time + timedelta(hours=1)).isoformat(),
        },
        {
            "asset_id": "ASSET_003",
            "name": "NBA Playoffs Dunk Compilation",
            "owner_org": "National Basketball Association",
            "phash": "c8e5f4a3b2d9c0e7",
            "histogram_sig": "0.09,0.11,0.13,0.20,0.17,0.12,0.08,0.10",
            "registered_at": (base_time + timedelta(hours=2)).isoformat(),
        },
    ]

    for a in assets:
        meta_str = a["name"] + a["owner_org"] + a["registered_at"]
        a["metadata_sha"] = hashlib.sha256(meta_str.encode()).hexdigest()
        a["dna_combined"] = f"{a['phash']}|{a['histogram_sig']}|{a['metadata_sha']}"

        cursor.execute("""
            INSERT INTO asset_registry
            (asset_id, name, owner_org, phash, histogram_sig, metadata_sha, dna_combined, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a["asset_id"], a["name"], a["owner_org"],
            a["phash"], a["histogram_sig"], a["metadata_sha"],
            a["dna_combined"], a["registered_at"]
        ))

    # ---- Custody Ledger ----
    events = [
        {
            "asset_id": "ASSET_001",
            "event_type": "licensed",
            "recipient": "Star Sports India",
            "notes": "Exclusive broadcast rights for 48 hours",
            "timestamp": (base_time + timedelta(hours=3)).isoformat(),
        },
        {
            "asset_id": "ASSET_001",
            "event_type": "distributed",
            "recipient": "Hotstar Streaming Platform",
            "notes": "Digital streaming distribution",
            "timestamp": (base_time + timedelta(hours=4)).isoformat(),
        },
        {
            "asset_id": "ASSET_001",
            "event_type": "violated",
            "recipient": "Unknown - Telegram Channel @sportleaks",
            "notes": "Unauthorized upload detected, resized to 480p",
            "timestamp": (base_time + timedelta(hours=9)).isoformat(),
        },
        {
            "asset_id": "ASSET_002",
            "event_type": "licensed",
            "recipient": "Sky Sports UK",
            "notes": "Match day highlight package",
            "timestamp": (base_time + timedelta(hours=2)).isoformat(),
        },
        {
            "asset_id": "ASSET_002",
            "event_type": "distributed",
            "recipient": "BBC Sport Online",
            "notes": "Web clip rights for 24 hours",
            "timestamp": (base_time + timedelta(hours=5)).isoformat(),
        },
        {
            "asset_id": "ASSET_003",
            "event_type": "licensed",
            "recipient": "ESPN Networks",
            "notes": "Full broadcast and digital rights",
            "timestamp": (base_time + timedelta(hours=3, minutes=30)).isoformat(),
        },
    ]

    for e in events:
        fields = [e["asset_id"], e["event_type"], e["recipient"], e["notes"], e["timestamp"]]
        e["hmac_sig"] = compute_hmac(fields)

        cursor.execute("""
            INSERT INTO custody_ledger
            (asset_id, event_type, recipient, notes, timestamp, hmac_sig)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            e["asset_id"], e["event_type"], e["recipient"],
            e["notes"], e["timestamp"], e["hmac_sig"]
        ))

    # ---- Bait Log ----
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
        cursor.execute("""
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
    print(f"[OK] Seeded demo data: {len(assets)} assets, {len(events)} custody events, {len(baits)} baits")


if __name__ == "__main__":
    seed()
