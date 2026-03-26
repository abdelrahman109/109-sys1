#!/usr/bin/env bash
set -e
cd /home/ubuntu/109-sys
source .venv/bin/activate
python - <<'PY'
from app import create_app
from app.db import create_backup
app = create_app()
with app.app_context():
    print(create_backup(app))
PY
