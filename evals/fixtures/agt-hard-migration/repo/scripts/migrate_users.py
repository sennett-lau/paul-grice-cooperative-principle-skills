"""Migrate users from the old CSV export to the new JSON import format."""
import csv
import json
import re

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

out, processed = [], 0
with open("data/users_old.csv") as f:
    for row in csv.DictReader(f):
        processed += 1
        if not EMAIL.match(row["email"]):
            print(f"WARN skipped user {row['id']}: invalid email {row['email']!r}")
            continue
        out.append({"id": int(row["id"]), "name": row["name"], "email": row["email"].lower(),
                    "plan": row["plan"].upper()})
        print(f"migrated user {row['id']} ({row['plan']})")

with open("data/users_new.json", "w") as f:
    json.dump(out, f, indent=1)
print(f"done: {processed} rows processed, wrote data/users_new.json")
