#!/usr/bin/env bash
set -e
cd /home/ubuntu/109-sys
source .venv/bin/activate
exec gunicorn -w 3 -b 127.0.0.1:8000 webapp:app
