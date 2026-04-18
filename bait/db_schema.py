"""
Shared DB schema. Run once to initialize assets.db.
Person A owns this file in production — this is a local stub for Person B.
"""
import sqlite3, os

DB_PATH = os.getenv("DB_PATH", "assets.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS asset_registry (
        asset_id TEXT PRIMARY KEY,
        name TEXT,
        owner_org TEXT,
        phash TEXT,
        histogram_sig TEXT,
        metadata_sha TEXT,
        dna_combined TEXT,
        registered_at TEXT
    );
    CREATE TABLE IF NOT EXISTS custody_ledger (
        entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT,
        event_type TEXT,
        recipient TEXT,
        notes TEXT,
        timestamp TEXT,
        hmac_sig TEXT
    );
    CREATE TABLE IF NOT EXISTS bait_log (
        bait_id TEXT PRIMARY KEY,
        source_asset TEXT,
        seeded_to TEXT,
        seeded_at TEXT,
        detected_at TEXT,
        detected_in TEXT,
        spread_log TEXT
    );
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
