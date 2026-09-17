"""Tests for the mutation tester.

The decisive pair: a *weak* suite must let a real bug survive (the tool reports
the blind spot), and a *strong* suite must kill it (the tool does not cry wolf).
"""

import unittest

from auditkit.checks import mutants
from auditkit.checks.mutants import generate_mutants, run_mutation_tests

TARGET = '''
def apply_fee(cash, notional, fee_rate):
    cash = cash - notional * fee_rate
    return cash
'''

TARGET_WITH_BRANCHES = '''
def size(capital, risk, atr, max_atr):
    if atr <= 0:
        return 0
    if atr > max_atr:
        return 0
    return capital * risk * (1 - atr / max_atr)
'''


def weak_suite(ns):
    """Only probes the zero-fee edge case -> it cannot see the fee line vanish."""
    f = ns["apply_fee"]
    assert f(100.0, 1000.0, 0.0) == 100.0


def strong_suite(ns):
    f = ns["apply_fee"]
    assert f(100.0, 1000.0, 0.0) == 100.0
    assert f(100.0, 1000.0, 0.01) == 90.0
    assert f(50.0, 2000.0, 0.005) == 40.0


class TestMutationTesting(unittest.TestCase):
    def test_weak_suite_leaves_blind_spot(self):
        result = run_mutation_tests(TARGET, weak_suite)
        self.assertGreater(len(result.survived), 0)
        self.assertTrue(
            any(m.kind == "delete_fee" for m in result.survived),
            msg=result.report(),
        )

    def test_strong_suite_kills_every_mutant(self):
        result = run_mutation_tests(TARGET, strong_suite)
        self.assertEqual(result.survived, [], msg=result.report())
        self.assertEqual(result.score, 1.0)

    def test_generates_all_mutation_kinds(self):
        kinds = {m.kind for m in generate_mutants(TARGET_WITH_BRANCHES)}
        self.assertIn("compare", kinds)
        self.assertIn("offbyone", kinds)
        self.assertIn("swap", kinds)

    def test_mutants_are_syntactically_valid(self):
        for m in generate_mutants(TARGET_WITH_BRANCHES):
            compile(m.source, "<mutant>", "exec")  # must not raise


if __name__ == "__main__":
    unittest.main()
