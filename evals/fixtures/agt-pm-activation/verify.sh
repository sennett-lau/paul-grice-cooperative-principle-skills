#!/bin/sh
echo "## activation rate before (4 weeks) and after (2 weeks) 2026-10-19"
python3 - <<'PY'
import csv
rows = list(csv.DictReader(open("data/activation.csv")))
def rate(rs): return sum(int(r["activated"]) for r in rs) / sum(int(r["signups"]) for r in rs)
print(f"before: {rate(rows[:4]):.1%}  after: {rate(rows[4:]):.1%}")
PY
