#!/bin/sh
echo "## tests"
python3 -m unittest 2>&1 | tail -1
echo "## does the untested cron script still run? (python3 scripts/nightly_report.py)"
python3 scripts/nightly_report.py 2>&1 | tail -1
echo "## diff"
git diff --stat
git status --short
