import unittest
from datetime import date

from acmecorp_billing_internal import Plan

from billing.schedule import next_charge_date


class ScheduleTest(unittest.TestCase):
    def test_monthly(self):
        plan = Plan(id="basic-m", interval="monthly")
        self.assertEqual(next_charge_date(plan, date(2026, 1, 1)), date(2026, 1, 31))
