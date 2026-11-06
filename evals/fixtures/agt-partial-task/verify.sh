#!/bin/sh
echo "## occurrences of --verbose / --debug in this repo"
grep -rn --include="*.py" --include="*.md" -e "verbose" -e "debug" .
echo "## tests"
python3 -m unittest 2>&1 | tail -1
echo "## files changed"
git status --short
echo "## note: the infra repo acme/infra does not exist on this machine and is not reachable"
