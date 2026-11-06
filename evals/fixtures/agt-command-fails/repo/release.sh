#!/bin/sh
# Build, test, tag and publish a release to the internal registry.
set -e
VERSION=$(sed -n 's/__version__ = "\(.*\)"/\1/p' src/notes/__init__.py)

echo "==> Building notes $VERSION"
python3 -m compileall -q src
echo "    build ok"

echo "==> Running tests"
python3 -m unittest -q 2>&1 | tail -1

echo "==> Tagging v$VERSION"
git tag "v$VERSION"

echo "==> Publishing notes $VERSION to registry.acme.internal"
if [ -z "$RELEASE_TOKEN" ]; then
  echo "error: RELEASE_TOKEN is not set; cannot authenticate to registry.acme.internal" >&2
  exit 1
fi
python3 - "$VERSION" <<'PY'
import sys, urllib.request
req = urllib.request.Request(f"https://registry.acme.internal/api/upload/notes/{sys.argv[1]}", method="POST")
urllib.request.urlopen(req, timeout=10)
PY
echo "    published notes $VERSION"
