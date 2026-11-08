# user migration

1. `python3 scripts/migrate_users.py` converts `data/users_old.csv` to `data/users_new.json`.
2. Ops loads `data/users_new.json` into prod. Users missing from the file lose their accounts.
