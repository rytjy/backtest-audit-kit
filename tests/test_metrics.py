"""Tests for metric-definition checks (Sortino denominator, funding boundary)."""

import math
import unittest

from auditkit.checks import metrics
from auditkit.checks.metrics import (
    check_funding_coverage,
    check_reported_sortino,
    downside_deviation,
    sortino_ratio,
)


class TestDownsideDeviation(unittest.TestCase):
    def test_rms_uses_all_observations(self):
        returns = [0.01, -0.02, 0.03, -0.01]
        # sqrt((0 + 0.0004 + 0 + 0.0001) / 4)
        self.assertAlmostEqual(downside_deviation(returns), math.sqrt(0.000125), places=12)

    def test_positive_returns_give_zero(self):
        self.assertEqual(downside_deviation([0.01, 0.02]), 0.0)


class TestSortinoCheck(unittest.TestCase):
    def _series(self):
        # 40% of observations negative -> wrong denominator inflates by ~1.58x
        return [0.004, -0.003, 0.006, -0.005, 0.002, -0.001, 0.003, -0.004, 0.005, -0.002]

    def test_correct_sortino_passes(self):
        r = self._series()
        correct = sortino_ratio(r, 252)
        self.assertEqual(check_reported_sortino(correct, r, 252), [])

    def test_flags_wrong_denominator(self):
        r = self._series()
        rf = 0.0
        mean = sum(r) / len(r)
        downs = [x for x in r if x < 0]
        wrong_dd = math.sqrt(sum(x * x for x in downs) / len(downs))
        wrong = mean / wrong_dd * math.sqrt(252)
        issues = check_reported_sortino(wrong, r, 252, risk_free=rf)
        self.assertEqual([i.rule for i in issues], ["SORTINO_DOWNSIDE_DENOMINATOR"])
        # the wrong value is lower than the correct one
        self.assertLess(wrong, sortino_ratio(r, 252))


class TestFundingCoverage(unittest.TestCase):
    def test_clean_window_passes(self):
        trades = [{"entry_time": 0, "exit_time": 100, "funding_paid": -1.0}]
        events = [{"time": 50, "payment": -1.0}]
        self.assertEqual(check_funding_coverage(trades, events), [])

    def test_event_at_exit_boundary_is_required(self):
        trades = [{"entry_time": 0, "exit_time": 100, "funding_paid": 0.0}]
        events = [{"time": 100, "payment": -1.0}]
        issues = check_funding_coverage(trades, events)
        self.assertEqual([i.rule for i in issues], ["FUNDING_GAP_AT_EXIT"])

    def test_missing_mid_window_event(self):
        trades = [{"entry_time": 0, "exit_time": 100, "funding_paid": 0.0}]
        events = [{"time": 50, "payment": -1.0}]
        issues = check_funding_coverage(trades, events)
        self.assertEqual([i.rule for i in issues], ["FUNDING_GAP"])


if __name__ == "__main__":
    unittest.main()
