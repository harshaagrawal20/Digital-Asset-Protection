"""
telegram_monitor.py — Telegram bot that watches groups for bait images.
Requires: BOT_TOKEN and ADMIN_CHAT_ID in .env
Run: python telegram_monitor.py
"""
import os, logging, asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from bait_generator import extract_bait_id
from bait_registry import mark_detected, append_spread
from alert_system import fire_alert
from spread_tracker import log_spread_sighting

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # optional; for alert DMs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_seen: set[tuple] = set()  # dedup: (bait_id, chat_name)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.photo:
        return

    chat_name = msg.chat.title or str(msg.chat.id)
    photo = msg.photo[-1]  # largest size
    file = await context.bot.get_file(photo.file_id)

    tmp_path = f"/tmp/{photo.file_id}.jpg"
    await file.download_to_drive(tmp_path)

    bait_id = extract_bait_id(tmp_path)

    try:
        os.remove(tmp_path)
    except OSError:
        pass

    if not bait_id:
        return

    key = (bait_id, chat_name)
    if key in _seen:
        log.info(f"Dedup skip: {bait_id} in {chat_name}")
        return
    _seen.add(key)

    log.info(f"Bait detected: {bait_id} in [{chat_name}]")

    # First-time detection
    updated = mark_detected(bait_id, chat_name)
    if updated:
        fire_alert(bait_id, chat_name)
    else:
        # Subsequent sighting — propagation
        append_spread(bait_id, chat_name)
        log_spread_sighting(bait_id, chat_name)
        log.info(f"Propagation sighting logged: {bait_id} → {chat_name}")

    # Optionally DM admin
    if ADMIN_CHAT_ID:
        status = "FIRST DETECTION" if updated else "SPREAD SIGHTING"
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"🚨 [{status}] Bait `{bait_id}` spotted in *{chat_name}*",
                parse_mode="Markdown",
            )
        except Exception as e:
            log.warning(f"Could not DM admin: {e}")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set in .env")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    log.info("Bot running — listening for bait images...")
    app.run_polling()


if __name__ == "__main__":
    main()
