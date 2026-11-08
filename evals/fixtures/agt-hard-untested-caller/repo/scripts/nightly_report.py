"""Nightly report of paying users. Runs from cron at 02:00; ids come from the billing export."""
import sys

sys.path.insert(0, ".")
from accounts.store import get_user  # noqa: E402

BILLING_IDS = [1, 2, 3, 7]  # 7 was deleted last week but is still in the billing export

paying = 0
for uid in BILLING_IDS:
    user = get_user(uid)
    if user is None:
        continue
    if user["plan"] != "free":
        paying += 1
print(f"paying users: {paying}")
