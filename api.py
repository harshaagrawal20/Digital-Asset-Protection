"""
Person A's API -- Mock implementation for Person C's dashboard.
Replace these with real imports from Person A's module on Day 2.

Function signatures locked at Day 1 morning:
  - get_asset_list()
  - get_custody_trail(asset_id)
  - verify_image(image_path)
"""

import sqlite3
import hashlib
import os
from db_schema import get_connection


def get_asset_list():
    """
    Return all registered assets from the asset_registry table.
    Returns: list of dicts, each with all asset_registry columns.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM asset_registry ORDER BY registered_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_custody_trail(asset_id: str):
    """
    Return the full chain of custody for a given asset.
    Returns: list of dicts from custody_ledger, ordered by timestamp.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM custody_ledger WHERE asset_id = ? ORDER BY timestamp ASC",
        (asset_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def verify_image(image_path: str):
    """
    Verify an uploaded image against the asset registry.
    In the real implementation (Person A), this computes pHash + histogram
    and matches against registered assets.

    Mock implementation: returns a match against ASSET_001 with high confidence
    to demonstrate the dashboard flow.

    Returns: dict with keys:
        - matched (bool)
        - asset_id (str or None)
        - asset_name (str or None)
        - confidence (float 0-1)
        - phash_distance (int)
        - details (str)
    """
    if not image_path or not os.path.exists(image_path):
        return {
            "matched": False,
            "asset_id": None,
            "asset_name": None,
            "confidence": 0.0,
            "phash_distance": -1,
            "details": "File not found or invalid path."
        }

    # Mock: always match to ASSET_001 for demo purposes
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM asset_registry WHERE asset_id = 'ASSET_001'")
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "matched": True,
            "asset_id": row["asset_id"],
            "asset_name": row["name"],
            "confidence": 0.94,
            "phash_distance": 3,
            "details": "Perceptual hash match found. Hamming distance: 3 (threshold: 10). "
                       "Histogram correlation: 0.91. Image appears to be a resized/compressed copy."
        }

    return {
        "matched": False,
        "asset_id": None,
        "asset_name": None,
        "confidence": 0.0,
        "phash_distance": -1,
        "details": "No matching asset found in registry."
    }
