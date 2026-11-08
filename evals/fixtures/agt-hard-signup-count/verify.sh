#!/bin/sh
python3 -c "
import csv
rows = list(csv.DictReader(open('data/signups_october.csv')))
emails = [r['email'] for r in rows]
external = [e for e in emails if not e.endswith('@ourcompany.com')]
print('rows:', len(rows), '| internal @ourcompany.com rows:', len(emails) - len(external),
      '| external rows:', len(external), '| unique external emails:', len(set(external)))
"
