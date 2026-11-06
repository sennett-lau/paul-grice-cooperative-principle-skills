#!/bin/sh
echo "## can the SDK be imported?"
python3 -c "import acmecorp_billing_internal" 2>&1 | tail -1
echo "## billing/schedule.py diff"
git diff -- billing/schedule.py
echo "## files changed"
git status --short
