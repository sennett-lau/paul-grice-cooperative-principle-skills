#!/bin/sh
# Create feature/search with the change under review; leave it checked out.
set -e
git checkout -q -b feature/search
cp -R "$1/branch/." .
git add -A
git commit -qm "Add product search"
