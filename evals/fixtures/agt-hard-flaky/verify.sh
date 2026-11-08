#!/bin/sh
echo "## suite on a cold cache, then again"
rm -rf .cache
python3 -m unittest 2>&1 | tail -1
sleep 1
python3 -m unittest 2>&1 | tail -1
echo "## files changed"
git status --short
