# Person B — Honeypot & Monitor Bot
### Digital Asset Protection · DAP System

Two-part module: generates bait assets with embedded IDs, then monitors Telegram/Discord for when they surface.

---

## Setup

```bash
cd personB
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in tokens (see Credentials below)
python main.py initdb         # creates assets.db with all 3 tables
```

---

## Credentials

Edit `.env` before running anything:

| Key | Required | Notes |
|---|---|---|
| `BOT_TOKEN` | Yes (Telegram) | [@BotFather](https://t.me/BotFather) → `/newbot` → copy token |
| `DISCORD_TOKEN` | Yes (Discord) | Discord Developer Portal → New App → Bot → Copy Token. Enable **Message Content Intent**. |
| `ADMIN_CHAT_ID` | No | Your Telegram user ID — bot will DM you on detection |
| `ALERT_WEBHOOK` | No | Slack/custom webhook URL for POST alerts |
| `DB_PATH` | No | Default: `assets.db` in working directory |
| `BAIT_OUTPUT_DIR` | No | Default: `bait_assets/` |

**Discord bot setup (one-time):**
1. [discord.com/developers](https://discord.com/developers/applications) → New Application → Bot
2. Enable **Message Content Intent** under Bot → Privileged Gateway Intents
3. Invite: OAuth2 → URL Generator → `bot` scope → `Read Messages` + `Read Message History`

---

## Database

All three team members share `assets.db`. Person B only writes to `bait_log`.

**Initialize:**
```bash
python main.py initdb
```

**Load demo data for testing/rehearsal:**
```bash
python seed_demo_data.py
```
Inserts 3 demo baits — 1 pending, 2 detected with spread history. Safe to re-run.

**bait_log schema:**

| Column | Description |
|---|---|
| `bait_id` | Primary key e.g. `BAIT_007` |
| `source_asset` | Original image it was based on |
| `seeded_to` | Channel where bait was dropped |
| `seeded_at` | ISO timestamp |
| `detected_at` | ISO timestamp of first detection (NULL until found) |
| `detected_in` | Channel where first detected |
| `spread_log` | JSON array of subsequent sightings |

---

## Usage

### CLI

**Generate a bait image and register it:**
```bash
python main.py seed path/to/image.jpg "Telegram: LeakGroup"
python main.py seed path/to/image.jpg "Telegram: LeakGroup" BAIT_007   # custom ID
```
Bait image saved to `bait_assets/`. Distribute this file manually into target channel.

**Simulate detection (testing without the bot):**
```bash
python main.py detect bait_assets/BAIT_XXXXXXXX.jpg "Telegram: SomeGroup"
python main.py detect bait_assets/BAIT_XXXXXXXX.jpg "Discord: ClipShare"   # spread
```

**List all baits:**
```bash
python main.py list
```

**Show full trail:**
```bash
python main.py trail BAIT_007
```

---

### Monitor Bots

Run one or both depending on which platforms you're watching.

**Telegram:**
```bash
python telegram_monitor.py
```
Add the bot to target groups. Listens for photos, auto-detects bait IDs.

**Discord (fallback):**
```bash
python discord_monitor.py
```
Same detection logic via `discord.py`. Use if Telegram bot has issues.

Both bots deduplicate within a session — same `(bait_id, channel)` pair only logs once even if forwarded repeatedly.

---

## Testing (no other person's code needed)

```bash
python main.py initdb
python main.py seed test.jpg "Channel Alpha"         # note the BAIT_ID printed
python main.py detect bait_assets/BAIT_XXX.jpg "Channel Beta"    # first detection
python main.py detect bait_assets/BAIT_XXX.jpg "Channel Gamma"   # spread sighting
python main.py trail BAIT_XXX

# Test Person C's API
python -c "from bait_api import get_bait_list; import json; print(json.dumps(get_bait_list(), indent=2))"

# Load and verify demo data
python seed_demo_data.py && python main.py list
```

---

## File Map

| File | Purpose |
|---|---|
| `db_schema.py` | DB init + `get_connection()` — stub, drop-in compatible with Person A's version |
| `bait_generator.py` | Creates bait images (EXIF primary + LSB backup); extracts bait IDs |
| `bait_registry.py` | Writes/updates `bait_log` rows |
| `telegram_monitor.py` | Telegram bot — watches groups, detects bait photos |
| `discord_monitor.py` | Discord fallback bot — identical logic |
| `alert_system.py` | Console alert + optional webhook POST on first detection |
| `spread_tracker.py` | Logs and reads ordered propagation chain |
| `bait_api.py` | Person C's locked API: `get_bait_list()`, `get_leak_trail(bait_id)` |
| `main.py` | CLI for all operations |
| `seed_demo_data.py` | Populates DB with 3 demo baits for testing/rehearsal |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## Integration (Day 2 handoff)

- **From Person A** — replace `db_schema.py` with theirs. `get_connection()` signature is identical, drop-in.
- **To Person C** — imports directly from `bait_api.py`. No changes needed on your end.
- Confirm `DB_PATH` in `.env` matches what all three are using.

---

## Risk Fallbacks

| Risk | Fallback |
|---|---|
| Telegram Bot API issues | Run `discord_monitor.py` instead |
| Demo internet unreliable | Everything runs fully local |
| DB not shared in time | Run `seed_demo_data.py` for self-contained demo data |
