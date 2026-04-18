"""
alert_system.py — Console + optional webhook alert on bait detection.
"""
import os, json, logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)
ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK")  # optional POST endpoint


def fire_alert(bait_id: str, detected_in: str):
    """Print alert to console and optionally POST to webhook."""
    timestamp = datetime.now(timezone.utc).isoformat()
    msg = (
        f"\n{'='*55}\n"
        f"  🚨 BAIT DETECTED\n"
        f"  Bait ID   : {bait_id}\n"
        f"  Channel   : {detected_in}\n"
        f"  Time (UTC): {timestamp}\n"
        f"{'='*55}\n"
    )
    print(msg)
    log.warning(f"BAIT DETECTED — {bait_id} in {detected_in}")

    if ALERT_WEBHOOK:
        try:
            import urllib.request
            payload = json.dumps({
                "bait_id": bait_id,
                "detected_in": detected_in,
                "detected_at": timestamp,
            }).encode()
            req = urllib.request.Request(
                ALERT_WEBHOOK,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            log.warning(f"Webhook alert failed: {e}")
