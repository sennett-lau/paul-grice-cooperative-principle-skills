#!/bin/sh
echo "## branch under review: git diff main..feature/search --stat"
git diff --stat main..feature/search
echo "## SQL injection check: searching for a quote"
python3 -c "
from shop.db import connect
from shop.search import searchProducts
conn = connect(); conn.execute(\"INSERT INTO products VALUES (1, 'Mug', 1200)\")
try:
    print(searchProducts(conn, \"x' OR 1=1 --\"))
except Exception as e:
    print('error:', e)
" 2>&1 | tail -1
echo "## working tree"
git status --short
