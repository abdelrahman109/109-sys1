#!/usr/bin/env bash
set -e
if [ -z "$1" ]; then
  echo "Usage: restore_db.sh /path/to/backup.db"
  exit 1
fi
cp "$1" /home/ubuntu/109-sys/instance/donations.db
echo "Database restored from $1"
