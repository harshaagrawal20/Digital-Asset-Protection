import cv2, hashlib, numpy as np
from PIL import Image
import imagehash

def _phash(image_path: str) -> str:
    img = Image.open(image_path).convert("RGB")
    return str(imagehash.phash(img))

def _histogram_sig(image_path: str) -> str:
    img = cv2.imread(image_path)
    sig_parts = []
    for i, ch in enumerate(["B", "G", "R"]):
        hist = cv2.calcHist([img], [i], None, [64], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        # Quantize to 3 decimal places for a compact, stable string
        sig_parts.append(",".join(f"{v:.3f}" for v in hist[:16]))
    return "|".join(sig_parts)

def _metadata_sha(name: str, owner: str, registered_at: str) -> str:
    raw = f"{name}::{owner}::{registered_at}"
    return hashlib.sha256(raw.encode()).hexdigest()

def generate_dna(image_path: str, name: str, owner: str, registered_at: str) -> dict:
    ph = _phash(image_path)
    hs = _histogram_sig(image_path)
    ms = _metadata_sha(name, owner, registered_at)
    return {
        "phash": ph,
        "histogram_sig": hs,
        "metadata_sha": ms,
        "dna_combined": f"{ph}|{hs}|{ms}"
    }

def compare_dna(dna1: str, dna2: str, threshold: int = 12) -> dict:
    """Compare two dna_combined strings. Returns match result."""
    p1, h1, _ = dna1.split("|", 2)
    p2, h2, _ = dna2.split("|", 2)
    ph1 = imagehash.hex_to_hash(p1)
    ph2 = imagehash.hex_to_hash(p2)
    hamming = ph1 - ph2
    match = hamming <= threshold
    return {"match": match, "hamming_distance": hamming, "threshold": threshold}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fingerprint.py <image_path>")
        sys.exit(1)
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    dna = generate_dna(sys.argv[1], "test_asset", "TestOrg", ts)
    print(f"pHash:         {dna['phash']}")
    print(f"Histogram:     {dna['histogram_sig'][:60]}...")
    print(f"Metadata SHA:  {dna['metadata_sha']}")
