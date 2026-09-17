"""Tests for fee / funding / slippage checks."""

import unittest

from auditkit.checks import fees
from auditkit.checks.fees import check_trades


class TestFeeChecks(unittest.TestCase):
    def test_clean_trades_have_no_issues(self):
        trades = [
            {"id": "a", "entry_notional": 10_000, "exit_notional": 10_000,
             "holding_bars": 8, "fee_paid": 10.0, "funding_paid": 8.0,
             "slippage_paid": 4.0},
            {"id": "b", "entry_notional": 5_000, "exit_notional": 5_000,
             "holding_bars": 1, "fee_paid": 5.0, "funding_paid": 0.5,
             "slippage_paid": 2.0},
        ]
        self.assertEqual(check_trades(trades), [])

    def test_catches_one_sided_fee(self):
        trades = [
            {"id": "fee1", "entry_notional": 10_000, "exit_notional": 10_000,
             "holding_bars": 8, "fee_paid": 5.0, "funding_paid": 8.0,
             "slippage_paid": 4.0},
        ]
        rules = {i.rule for i in check_trades(trades)}
        self.assertIn("ONE_SIDED_FEE", rules)

    def test_catches_funding_charged_once(self):
        trades = [
            {"id": "fund1", "entry_notional": 10_000, "exit_notional": 10_000,
             "holding_bars": 8, "fee_paid": 10.0, "funding_paid": 1.0,
             "slippage_paid": 4.0},
        ]
        rules = {i.rule for i in check_trades(trades)}
        self.assertIn("FUNDING_ONCE", rules)

    def test_catches_double_counted_slippage(self):
        trades = [
            {"id": "slip1", "entry_notional": 10_000, "exit_notional": 10_000,
             "holding_bars": 8, "fee_paid": 10.0, "funding_paid": 8.0,
             "slippage_paid": 8.0},
        ]
        rules = {i.rule for i in check_trades(trades)}
        self.assertIn("SLIPPAGE_MULTIPLE", rules)

    def test_missing_fields_are_not_flagged(self):
        # A trade that simply does not report funding must not be a false alarm.
        trades = [{"id": "partial", "entry_notional": 10_000,
                   "exit_notional": 10_000, "fee_paid": 10.0}]
        self.assertEqual(check_trades(trades), [])


if __name__ == "__main__":
    unittest.main()
