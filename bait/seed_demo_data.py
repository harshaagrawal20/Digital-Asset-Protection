"""
seed_demo_data.py — Populate assets.db with realistic demo data.
Run: python seed_demo_data.py
"""
from db_schema import init_db, get_connection
import json

BAITS = [
    ("BAIT_001", "match_clip_finals.jpg", "Telegram: LeakZone Alpha",
     "2024-01-15T10:00:00+00:00", "2024-01-15T10:47:00+00:00", "Telegram: SportsDump",
     [{"channel": "Discord: ClipShare", "seen_at": "2024-01-15T11:10:00+00:00"},
      {"channel": "Telegram: ViralClips", "seen_at": "2024-01-15T11:45:00+00:00"}]),
    ("BAIT_002", "press_conference_raw.jpg", "Discord: MediaLeaks",
     "2024-01-15T09:00:00+00:00", None, None, []),
    ("BAIT_003", "halftime_highlights.jpg", "Telegram: InsiderGroup",
     "2024-01-14T14:00:00+00:00", "2024-01-14T16:22:00+00:00", "Telegram: FootballLeaks",
     [{"channel": "Telegram: GoalAlerts", "seen_at": "2024-01-14T17:05:00+00:00"}]),
]

init_db()
conn = get_connection()
conn.execute("DELETE FROM bait_log")  # clean slate
for b in BAITS:
    conn.execute(
        """INSERT INTO bait_log
           (bait_id, source_asset, seeded_to, seeded_at, detected_at, detected_in, spread_log)
           VALUES (?,?,?,?,?,?,?)""",
        (*b[:6], json.dumps(b[6]))
    )
conn.commit()
conn.close()
print(f"✓ Inserted {len(BAITS)} demo bait entries into assets.db")
