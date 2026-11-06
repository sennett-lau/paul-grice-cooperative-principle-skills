#!/bin/sh
echo "## python3 -m unittest -v"
python3 -m unittest -v 2>&1 | grep -E "\.\.\. |^Ran |^OK|^FAILED"
echo "## files changed"
git status --short
