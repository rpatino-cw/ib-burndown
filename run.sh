#!/bin/bash
# run.sh — One-command launcher for ib-lookup v2
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"

# Create venv + install deps if needed
if [ ! -d "$VENV" ]; then
  echo "Setting up virtual environment..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet -r "$DIR/requirements.txt"
fi

exec "$VENV/bin/python3" -m ib_lookup "$@"
