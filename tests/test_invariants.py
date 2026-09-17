"""Tests for ledger invariants."""

import unittest

from auditkit.checks import invariants
from auditkit.checks.invariants import check_ledger, violations_by_rule


def good_ledger():
    """A consistent run: two trades, one withdrawal, one bust that carries wd_cum."""
    return [
        {"step": 0, "cap": 100.0, "cash": 100.0, "positions": {}, "wd_cum": 0.0,
         "trades": 0},
        {"step": 1, "cap": 120.0, "cash": 70.0, "positions": {"BTC": 50.0},
         "wd_cum": 0.0, "trades": 1},
        {"step": 2, "cap": 110.0, "cash": 55.0, "positions": {"BTC": 55.0},
         "wd_cum": 10.0, "wd": 10.0, "trades": 2},
        # bust: capital reset to 100, but cumulative withdrawals are carried
        {"step": 3, "cap": 100.0, "cash": 100.0, "positions": {}, "wd_cum": 10.0,
         "bust": True, "trades": 2},
        {"step": 4, "cap": 105.0, "cash": 105.0, "positions": {}, "wd_cum": 10.0,
         "trades": 3},
    ]


class TestLedgerInvariants(unittest.TestCase):
    def test_clean_ledger_has_no_violations(self):
        self.assertEqual(check_ledger(good_ledger()), [])

    def test_catches_planted_violations(self):
        ledger = [
            {"step": 0, "cap": 100.0, "cash": 100.0, "positions": {}, "wd_cum": 10.0,
             "trades": 5},
            # withdrew 10 but wd_cum never grew
            {"step": 1, "cap": 90.0, "cash": 90.0, "positions": {}, "wd_cum": 10.0,
             "wd": 10.0, "trades": 6},
            # bust path dropped wd_cum back to 0
            {"step": 2, "cap": 100.0, "cash": 100.0, "positions": {}, "wd_cum": 0.0,
             "bust": True, "trades": 6},
            # equity identity broken + negative cash + counter goes backwards
            {"step": 3, "cap": 90.0, "cash": -5.0, "positions": {}, "wd_cum": 0.0,
             "trades": 3},
        ]
        rules = violations_by_rule(check_ledger(ledger))
        for expected in (
            "WD_ACCRUAL",
            "BUST_WD_CARRY",
            "EQUITY_IDENTITY",
            "NEGATIVE_BALANCE",
            "COUNTER_MONOTONIC",
        ):
            self.assertIn(expected, rules, msg=f"missed {expected}: {rules}")

    def test_catches_equity_identity_on_positions(self):
        ledger = [
            {"step": 0, "cap": 100.0, "cash": 60.0, "positions": {"BTC": 30.0}},
        ]
        rules = violations_by_rule(check_ledger(ledger))
        self.assertIn("EQUITY_IDENTITY", rules)

    def test_bust_without_wd_cum_key_is_flagged(self):
        ledger = [
            {"step": 0, "cap": 120.0, "cash": 120.0, "positions": {}, "wd_cum": 20.0},
            {"step": 1, "cap": 100.0, "cash": 100.0, "positions": {}, "bust": True},
        ]
        rules = violations_by_rule(check_ledger(ledger))
        self.assertIn("BUST_WD_CARRY", rules)


if __name__ == "__main__":
    unittest.main()
