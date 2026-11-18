"""Cost sensitivity sweep over take-profit and leverage.

    python3 -m auditkit.ledger sweep state.json --config strategy.json
    python3 -m auditkit.ledger sweep state.json --grid 1.5,3,8 --leverage 20,40

Answers one question: at this cost level, what break-even win rate does a given
take-profit / leverage pair require? Trades with entry_px/exit_px give the cost
in percent of notional; leverage turns it into percent of margin.
"""
from __future__ import annotations

from .cards import FEE_BPS_SIDE, SLIP_BPS_FILL

BPS = 10_000.0


def _signed_move(t):
    a = float(t.get("entry_px", 0) or 0)
    b = float(t.get("exit_px", 0) or 0)
    if a <= 0:
        return 0.0
    m = (b - a) / a
    return m if str(t.get("side", "")).lower() != "short" else -m


def cmd_sweep(state, config, grid, levs):
    trades = state.get("trades", [])
    if not trades:
        print("no trades")
        return 0
    moves = [100 * _signed_move(t) for t in trades]
    cost = 2 * (FEE_BPS_SIDE + SLIP_BPS_FILL) / 100.0
    net = [m - cost for m in moves]
    n = len(moves)
    wins0 = sum(1 for m in moves if m > 0)
    wins1 = sum(1 for m in net if m > 0)
    ordered = sorted(moves)
    median = ordered[n // 2] if n % 2 else 0.5 * (ordered[n // 2 - 1] + ordered[n // 2])
    print(f"round trip = {2*FEE_BPS_SIDE/100:.3f}% fees + {2*SLIP_BPS_FILL/100:.3f}% slippage = {cost:.3f}% of notional")
    print(f"trades={n}  price move mean={sum(moves)/n:+.4f}%  median={median:+.4f}%  best={max(moves):+.4f}%")
    print(f"wins before cost={wins0} ({100*wins0/n:.0f}%)   after cost={wins1} ({100*wins1/n:.0f}%)")
    print(f"sum before cost={sum(moves):+.2f}pp   after cost={sum(net):+.2f}pp")
    print()
    print(f"{'leverage':>8} {'cost % margin':>14} {'TP for BE @55% WR':>19} {'@60%':>8} {'@70%':>8}")
    for lev in levs:
        c = cost * lev
        print(f"{lev:>8} {c:>13.2f}% {c/0.10:>18.1f}% {c/0.20:>7.1f}% {c/0.40:>7.1f}%")
    print()
    for lev in levs:
        c = cost * lev
        print(f"leverage {lev}x  (round-trip cost = {c:.2f}% of margin)")
        for tp in grid:
            pstar = (tp + c) / (2 * tp) if tp > 0 else float("nan")
            print(f"   TP {tp:>5.1f}% margin -> win {tp-c:+6.2f}% / loss {-(tp+c):+6.2f}%   break-even WR {100*pstar:5.1f}%")
        print()
    return 0
