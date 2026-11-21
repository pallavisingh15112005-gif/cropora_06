#!/usr/bin/env bash
# Refresh the bundled Agmarknet snapshot and publish it to both deployments.
set -euo pipefail

cd "$(dirname "$0")/.."
python scripts/export_live_snapshot.py

if git diff --quiet -- data/live_snapshot.json; then
    echo "Nothing to publish."
    exit 0
fi

git add data/live_snapshot.json
git commit -m "Refresh live snapshot $(date +%F)"
git push
