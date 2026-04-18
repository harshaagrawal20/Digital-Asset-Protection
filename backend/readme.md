# Person A — DNA Engine & Custody Ledger

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # edit SIGNING_KEY
```

## CLI Usage
```bash
# Register an asset
python main.py register photo.jpg "Goal Clip – Final 2025" "SportsCorp"

# Log a distribution event
python main.py distribute ASSET_001 "ESPN India" licensed "Broadcast rights Q3"

# Verify a suspected copy
python main.py verify suspect_image.jpg

# View custody trail
python main.py trail ASSET_001

# Export evidence JSON
python main.py evidence ASSET_001
```

## File Map
| File | Purpose |
|------|---------|
| db_setup.py | Creates assets.db and all 3 tables |
| fingerprint.py | pHash + histogram + SHA DNA generation |
| register_asset.py | Registers new asset into DB |
| ledger.py | Logs + HMAC-signs distribution events |
| verify_asset.py | Matches suspect image against registry |
| evidence_export.py | Generates JSON evidence report |
| api.py | Clean interface for Person C's dashboard |
| main.py | CLI entry point |

## For Person C
Import only `api.py`:
```python
from api import get_asset_list, get_custody_trail_api, verify_image_api, export_evidence_api
```
