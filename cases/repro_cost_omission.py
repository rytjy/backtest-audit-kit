#!/usr/bin/env python3
"""Reproduce Case 5 — cost omission: the gross profit that fees eat.

A representative book of high-turnover, 50x round trips that recorded NO costs,
charged against the venue's real taker rate (4.5 bps/side), with funding and
slippage at tool defaults.

    python3 cases/repro_cost_omission.py

Anonymized: no venue, symbol or account data. The shape (749 round trips,
400 notional per side) mirrors a real audit.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auditkit.checks import fees

BPS = 10_000.0
NOTIONAL = 400.0
N = 749
LEV = 50.0
TP_PCT_OF_MARGIN = 4.0      # take-profit, percent of margin
FEE_BPS = 4.5               # taker, per side (venue rate)
ACCOUNT = 80.0

BOOK = [
    {
        "id": "t%d" % (i + 1),
        "entry_notional": NOTIONAL,
        "exit_notional": NOTIONAL,
        "holding_bars": 1 + (i % 4),
        "fee_paid": 0.0,
        "funding_paid": 0.0,
        "slippage_paid": 0.0,
    }
    for i in range(N)
]


def main():
    issues = fees.check_trades(BOOK)
    print("fees.check_trades() ->", len(issues), "issues")
    for rule, n in sorted(Counter(x.rule for x in issues).items()):
        print("  %-16s %d" % (rule, n))

    fee = sum((t['entry_notional'] + t['exit_notional']) * FEE_BPS / BPS for t in BOOK)
    fund = sum(t['entry_notional'] * 1.0 / BPS * t['holding_bars'] for t in BOOK)
    slip = sum((t['entry_notional'] + t['exit_notional']) * 2.0 / BPS for t in BOOK)
    total = fee + fund + slip

    print()
    print("cost at venue rate (fee 4.5bps/side); funding 1bp/bar + slippage 2bps/fill at tool default:")
    print("  fees     %8.1f" % fee)
    print("  funding  %8.1f" % fund)
    print("  slippage %8.1f" % slip)
    print("  TOTAL    %8.1f  (= %.1fx the %.0f-unit account)" % (total, total / ACCOUNT, ACCOUNT))

    tp_move = TP_PCT_OF_MARGIN / LEV       # percent price move to hit TP
    toll = 2 * FEE_BPS / BPS * 100.0        # round-trip fee, percent of notional
    print()
    print("take-profit needs a +%.2f%% price move; one round trip costs %.2f%%" % (tp_move, toll))
    print("=> %s" % ("target BELOW the toll: every win is a net loss" if tp_move < toll else "target above toll"))


if __name__ == "__main__":
    main()
