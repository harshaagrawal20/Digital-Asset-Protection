import sqlite3, os

DB_PATH = os.environ.get("DB_PATH", "assets.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS asset_registry (
            asset_id       TEXT PRIMARY KEY,
            name           TEXT NOT NULL,
            owner_org      TEXT NOT NULL,
            phash          TEXT NOT NULL,
            histogram_sig  TEXT NOT NULL,
            metadata_sha   TEXT NOT NULL,
            dna_combined   TEXT NOT NULL,
            registered_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS custody_ledger (
            entry_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id    TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            recipient   TEXT NOT NULL,
            notes       TEXT,
            timestamp   TEXT NOT NULL,
            hmac_sig    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bait_log (
            bait_id      TEXT PRIMARY KEY,
            source_asset TEXT,
            seeded_to    TEXT,
            seeded_at    TEXT,
            detected_at  TEXT,
            detected_in  TEXT,
            spread_log   TEXT DEFAULT '[]'
        );
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Initialized: {DB_PATH}")

if __name__ == "__main__":
    init_db()
