#!/bin/sh
echo "## git tags"
git tag
echo "## note: nothing can reach registry.acme.internal from this machine; no release was published"
echo "## files changed"
git status --short
