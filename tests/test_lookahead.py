"""Tests for the look-ahead detector.

Hard requirement: the detector must both *catch* a planted bug and stay *quiet*
on the fixed version. One test per side, minimum.
"""

import unittest
from pathlib import Path

from auditkit.checks import lookahead

FIXTURES = Path(__file__).parent / "fixtures"


class TestLookaheadDetection(unittest.TestCase):
    def test_catches_planted_lookahead(self):
        src = (FIXTURES / "lookahead_buggy.py").read_text(encoding="utf-8")
        findings = lookahead.detect(src)
        rules = {f.rule for f in findings}
        # the planted future-window scan on the entry bar
        self.assertIn("FUTURE_WINDOW_LOOP", rules)
        # the planted negative shift
        self.assertIn("NEGATIVE_SHIFT", rules)
        # the planted future slice
        self.assertIn("FUTURE_SLICE", rules)
        # nested scan must be escalated to HIGH
        self.assertTrue(any(f.severity == "HIGH" for f in findings))
        # and the window-loop finding must be the nested/high one
        win = [f for f in findings if f.rule == "FUTURE_WINDOW_LOOP"]
        self.assertTrue(all(f.severity == "HIGH" for f in win))

    def test_no_false_positive_on_fixed_version(self):
        src = (FIXTURES / "lookahead_fixed.py").read_text(encoding="utf-8")
        findings = lookahead.detect(src)
        self.assertEqual(findings, [], msg=lookahead.format_findings(findings))

    def test_positive_shift_is_clean(self):
        self.assertEqual(lookahead.detect("x = s.shift(1)"), [])
        self.assertEqual(lookahead.detect("x = s.pct_change(-1)")[0].rule, "NEGATIVE_SHIFT")

    def test_past_window_slice_is_clean(self):
        self.assertEqual(lookahead.detect("w = df['c'].iloc[i-24:i+1]"), [])
        self.assertEqual(
            lookahead.detect("w = df['c'].iloc[i+1:]")[0].rule, "FUTURE_SLICE"
        )

    def test_backward_window_with_plus_one_is_clean(self):
        """Regression for case 9: ``(i - n) + 1`` ends at or before the anchor."""
        src = (
            "for i in range(n, len(c)):\n"
            "    w = c[i-n+1:i+1]\n"
            "    x = sum(w)\n"
        )
        self.assertEqual(
            lookahead.detect(src), [], msg=lookahead.format_findings(lookahead.detect(src))
        )
        # a genuinely forward slice in the same loop must still be caught
        fwd = "for i in range(n, len(c)):\n    w = c[i+1:i+5]\n"
        self.assertEqual(lookahead.detect(fwd)[0].rule, "FUTURE_SLICE")
        # a net-positive offset still counts: (i - 3) + 5 == i + 2
        net = "for i in range(n, len(c)):\n    w = c[(i-3)+5:]\n"
        self.assertEqual(lookahead.detect(net)[0].rule, "FUTURE_SLICE")

    def test_standalone_forward_loop_is_medium_not_high(self):
        src = "for j in range(i+1, n):\n    x = data[j]\n"
        findings = lookahead.detect(src)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule, "FUTURE_WINDOW_LOOP")
        self.assertEqual(findings[0].severity, "MEDIUM")


if __name__ == "__main__":
    unittest.main()
