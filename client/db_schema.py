"""
Digital Asset Protection -- Shared Database Schema
Locked at Day 1 morning. No schema changes after 10am.
Creates assets.db with 3 tables: asset_registry, custody_ledger, bait_log.
"""

import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets.db"))


def get_connection():
    """Return a connection to the shared SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all three tables if they do not already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: asset_registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asset_registry (
            asset_id        TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            owner_org       TEXT NOT NULL,
            phash           TEXT,
            histogram_sig   TEXT,
            metadata_sha    TEXT,
            dna_combined    TEXT,
            registered_at   TEXT NOT NULL
        )
    """)

    # Table 2: custody_ledger
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custody_ledger (
            entry_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id    TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            recipient   TEXT,
            notes       TEXT,
            timestamp   TEXT NOT NULL,
            hmac_sig    TEXT NOT NULL,
            FOREIGN KEY (asset_id) REFERENCES asset_registry(asset_id)
        )
    """)

    # Table 3: bait_log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bait_log (
            bait_id       TEXT PRIMARY KEY,
            source_asset  TEXT NOT NULL,
            seeded_to     TEXT NOT NULL,
            seeded_at     TEXT NOT NULL,
            detected_at   TEXT,
            detected_in   TEXT,
            spread_log    TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
