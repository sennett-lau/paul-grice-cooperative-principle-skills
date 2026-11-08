#!/bin/sh
echo "## files changed"
git status --short
git diff --stat
