"""
bait_generator.py — Creates bait assets from real images.
Embeds unique BAIT_ID into EXIF and as LSB in pixels.
"""
import os, uuid
from PIL import Image, ImageFilter, ImageEnhance
import piexif

BAIT_OUTPUT_DIR = os.getenv("BAIT_OUTPUT_DIR", "bait_assets")
os.makedirs(BAIT_OUTPUT_DIR, exist_ok=True)


def _embed_lsb(img: Image.Image, bait_id: str) -> Image.Image:
    """Embed bait_id string into LSB of pixel red channel."""
    img = img.convert("RGB")
    pixels = list(img.getdata())
    payload = bait_id.encode() + b"\x00"  # null-terminated
    if len(payload) * 8 > len(pixels):
        raise ValueError("Image too small to embed bait ID via LSB.")
    new_pixels = list(pixels)
    for i, byte in enumerate(payload):
        for bit in range(8):
            px_idx = i * 8 + bit
            r, g, b = new_pixels[px_idx]
            bit_val = (byte >> (7 - bit)) & 1
            r = (r & 0xFE) | bit_val
            new_pixels[px_idx] = (r, g, b)
    out = img.copy()
    out.putdata(new_pixels)
    return out


def _embed_exif(img: Image.Image, bait_id: str) -> dict:
    """Return piexif-compatible exif dict with BAIT_ID in UserComment."""
    try:
        exif_dict = piexif.load(img.info.get("exif", b""))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
    # UserComment field (0x9286) — prefix with ASCII\0\0\0\0\0\0\0\0
    comment = b"ASCII\x00\x00\x00" + f"BAIT_ID:{bait_id}".encode()
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = comment
    return exif_dict


def generate_bait(source_image_path: str, bait_id: str = None) -> dict:
    """
    Creates a bait asset from source_image_path.
    Returns dict: {bait_id, bait_path, source_image_path}
    """
    if bait_id is None:
        bait_id = "BAIT_" + uuid.uuid4().hex[:8].upper()

    img = Image.open(source_image_path)

    # Apply slight perturbations so it looks natural
    img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
    img = ImageEnhance.Brightness(img).enhance(1.03)

    # LSB embed
    img_lsb = _embed_lsb(img, bait_id)

    # EXIF embed
    exif_dict = _embed_exif(img, bait_id)
    try:
        exif_bytes = piexif.dump(exif_dict)
    except Exception:
        exif_bytes = b""

    # Save
    ext = os.path.splitext(source_image_path)[1] or ".jpg"
    bait_filename = f"{bait_id}{ext}"
    bait_path = os.path.join(BAIT_OUTPUT_DIR, bait_filename)

    save_kwargs = {}
    if exif_bytes:
        save_kwargs["exif"] = exif_bytes
    img_lsb.save(bait_path, **save_kwargs)

    return {"bait_id": bait_id, "bait_path": bait_path, "source_image_path": source_image_path}


def extract_bait_id(image_path: str) -> str | None:
    """
    Try to extract BAIT_ID from an image (EXIF first, then LSB fallback).
    Returns bait_id string or None.
    """
    # --- EXIF approach ---
    try:
        img = Image.open(image_path)
        exif_bytes = img.info.get("exif", b"")
        if exif_bytes:
            exif_dict = piexif.load(exif_bytes)
            comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment, b"")
            if isinstance(comment, bytes) and b"BAIT_ID:" in comment:
                raw = comment.split(b"BAIT_ID:")[1].decode(errors="ignore").strip()
                return raw.split()[0]  # take first token
    except Exception:
        pass

    # --- LSB fallback ---
    try:
        img = Image.open(image_path).convert("RGB")
        pixels = list(img.getdata())
        bits = []
        for px in pixels[:2048]:
            bits.append(px[0] & 1)
        chars = []
        for i in range(0, len(bits) - 7, 8):
            byte = 0
            for b in range(8):
                byte = (byte << 1) | bits[i + b]
            if byte == 0:
                break
            chars.append(chr(byte))
        candidate = "".join(chars)
        if candidate.startswith("BAIT_"):
            return candidate
    except Exception:
        pass

    return None
