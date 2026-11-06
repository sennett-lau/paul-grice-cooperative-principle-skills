#!/bin/sh
echo "## python3 analysis.py"
python3 analysis.py
echo "## files changed"
git status --short
