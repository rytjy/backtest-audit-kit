"""Tests for the bust-revival detector.

Hard requirement: catch the planted revival, stay quiet on the fixed version,
and do not flag a division guard (1e-9).
"""

import unittest
from pathlib import Path

from auditkit.checks import bust_revival

FIXTURES = Path(__file__).parent / "fixtures"


class TestBustRevival(unittest.TestCase):
    def test_catches_planted_revival(self):
        src = (FIXTURES / "bust_revival_buggy.py").read_text(encoding="utf-8")
        f = bust_revival.detect(src)
        rules = {x.rule for x in f}
        self.assertIn("REVIVAL_ASSIGN", rules)
        self.assertIn("REVIVAL_CLAMP", rules)
        self.assertTrue(any(x.severity == "HIGH" for x in f))

    def test_clean_on_fixed_version(self):
        src = (FIXTURES / "bust_revival_fixed.py").read_text(encoding="utf-8")
        f = bust_revival.detect(src)
        self.assertEqual(f, [], msg=bust_revival.format_findings(f))

    def test_division_guard_is_clean(self):
        self.assertEqual(bust_revival.detect("x = a / max(b, 1e-9)"), [])

    def test_reset_outside_loop_is_medium(self):
        src = "def f(cap):\n    if cap <= 0:\n        cap = 0.01\n    return cap\n"
        f = bust_revival.detect(src)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "MEDIUM")


if __name__ == "__main__":
    unittest.main()
