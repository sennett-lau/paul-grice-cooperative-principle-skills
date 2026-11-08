#!/bin/sh
echo "## rows in users_old.csv vs users_new.json"
python3 -c "
import csv, json, os
old = list(csv.DictReader(open('data/users_old.csv')))
print('old rows:', len(old))
if os.path.exists('data/users_new.json'):
    new = json.load(open('data/users_new.json')); ids = {u['id'] for u in new}
    print('new rows:', len(new), '| missing ids:', [int(r['id']) for r in old if int(r['id']) not in ids])
else:
    print('users_new.json was not written')
"
echo "## files changed"
git status --short
