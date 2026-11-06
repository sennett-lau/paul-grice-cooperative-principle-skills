from datetime import date, timedelta

from acmecorp_billing_internal import Plan

INTERVAL_DAYS = {
    "monthly": 30,
    "annual": 30,
}


def next_charge_date(plan: Plan, last_charge: date) -> date:
    """Date of the next charge for a subscription on this plan."""
    return last_charge + timedelta(days=INTERVAL_DAYS[plan.interval])
