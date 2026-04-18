"""
discord_monitor.py — Discord fallback bot (same logic as telegram_monitor.py).
Requires: DISCORD_TOKEN in .env
Run: python discord_monitor.py
"""
import os, io, logging
import discord
from dotenv import load_dotenv
from bait_generator import extract_bait_id
from bait_registry import mark_detected, append_spread
from alert_system import fire_alert
from spread_tracker import log_spread_sighting

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# In-memory dedup: (bait_id, channel) pairs seen this session
_seen: set[tuple] = set()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    log.info(f"Discord bot ready: {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.attachments:
        return

    channel_name = f"Discord: {message.channel.name}"

    for attachment in message.attachments:
        if not attachment.content_type or not attachment.content_type.startswith("image"):
            continue

        data = await attachment.read()
        tmp_path = f"/tmp/{attachment.id}.jpg"
        with open(tmp_path, "wb") as f:
            f.write(data)

        bait_id = extract_bait_id(tmp_path)
        try:
            os.remove(tmp_path)
        except OSError:
            pass

        if not bait_id:
            continue

        key = (bait_id, channel_name)
        if key in _seen:
            log.info(f"Dedup skip: {bait_id} in {channel_name}")
            continue
        _seen.add(key)

        log.info(f"Bait detected: {bait_id} in [{channel_name}]")
        updated = mark_detected(bait_id, channel_name)
        if updated:
            fire_alert(bait_id, channel_name)
        else:
            append_spread(bait_id, channel_name)
            log_spread_sighting(bait_id, channel_name)


def main():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set in .env")
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
