"""Fee / funding / slippage accounting.

Costs are where optimistic backtests hide.  Three failure modes dominate:

* **one-sided fees** — the engine charges the entry fee but forgets the exit
  (or vice-versa), so every trade is quietly cheaper than reality;
* **funding charged once** — a perp position held for ``k`` bars should pay
  funding ``k`` times, but the engine deducts a single period;
* **double-counted slippage** — slippage is applied to both the raw fill *and*
  the already-slippaged price, charging it twice per fill.

Each trade is a ``dict``::

    {
      "id": "t1",
      "entry_notional": 10_000.0,
      "exit_notional": 10_000.0,   # optional, defaults to entry_notional
      "holding_bars": 8,
      "fee_paid": 10.0,            # total round-trip fee actually charged
      "funding_paid": 8.0,         # total funding actually charged
      "slippage_paid": 4.0,        # total slippage cost actually charged
    }

Rates are in **basis points** (1 bp = 0.01%).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

__all__ = ["FeeIssue", "check_trades", "check_trade", "DEFAULT_RATES"]

BPS = 10_000.0
DEFAULT_RATES = {
    "fee_bps": 5.0,            # per side (taker)
    "funding_bps_per_bar": 1.0,
    "slippage_bps": 2.0,       # per fill
}
REL_TOL = 0.05  # 5% tolerance on each estimate


@dataclass(frozen=True)
class FeeIssue:
    rule: str
    trade_id: object
    message: str
    expected: Optional[float] = None
    actual: Optional[float] = None

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "trade_id": self.trade_id,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
        }

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"[{self.rule}] trade={self.trade_id}: {self.message}"


def _f(trade: dict, key: str, default: float = 0.0) -> float:
    val = trade.get(key, default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _outside(actual: float, expected: float, rel_tol: float) -> Optional[str]:
    """Return ``"low"``, ``"high"``, or ``None`` relative to ``expected``."""
    if expected <= 0:
        return "high" if actual > 1e-9 else None
    ratio = actual / expected
    if ratio < 1 - rel_tol:
        return "low"
    if ratio > 1 + rel_tol:
        return "high"
    return None


def check_trade(
    trade: dict,
    fee_bps: float = DEFAULT_RATES["fee_bps"],
    funding_bps_per_bar: float = DEFAULT_RATES["funding_bps_per_bar"],
    slippage_bps: float = DEFAULT_RATES["slippage_bps"],
    rel_tol: float = REL_TOL,
) -> List[FeeIssue]:
    issues: List[FeeIssue] = []
    tid = trade.get("id", "?")
    entry = _f(trade, "entry_notional")
    exit_n = _f(trade, "exit_notional", entry) or entry
    bars = int(_f(trade, "holding_bars", 1)) or 1

    # --- round-trip fees (both sides) ------------------------------------- #
    expected_fee = (entry + exit_n) * fee_bps / BPS
    actual_fee = _f(trade, "fee_paid", float("nan"))
    if actual_fee == actual_fee:  # not NaN -> provided
        side = _outside(actual_fee, expected_fee, rel_tol)
        if side == "low":
            issues.append(
                FeeIssue(
                    "ONE_SIDED_FEE",
                    tid,
                    f"fee {actual_fee:.4f} < round-trip expectation "
                    f"{expected_fee:.4f} (entry+exit) -- likely only one side charged",
                    expected_fee,
                    actual_fee,
                )
            )
        elif side == "high":
            issues.append(
                FeeIssue(
                    "FEE_OVERCHARGE",
                    tid,
                    f"fee {actual_fee:.4f} > round-trip expectation {expected_fee:.4f}",
                    expected_fee,
                    actual_fee,
                )
            )

    # --- funding per bar -------------------------------------------------- #
    expected_funding = entry * funding_bps_per_bar / BPS * bars
    actual_funding = _f(trade, "funding_paid", float("nan"))
    if actual_funding == actual_funding and bars > 1:
        side = _outside(actual_funding, expected_funding, rel_tol)
        if side == "low":
            issues.append(
                FeeIssue(
                    "FUNDING_ONCE",
                    tid,
                    f"funding {actual_funding:.4f} for {bars} bars < "
                    f"{expected_funding:.4f} -- charged once, not per bar",
                    expected_funding,
                    actual_funding,
                )
            )
        elif side == "high":
            issues.append(
                FeeIssue(
                    "FUNDING_OVERCHARGE",
                    tid,
                    f"funding {actual_funding:.4f} > {expected_funding:.4f} "
                    f"for {bars} bars",
                    expected_funding,
                    actual_funding,
                )
            )

    # --- slippage once per fill (round trip = two fills) ------------------ #
    expected_slip = (entry + exit_n) * slippage_bps / BPS
    actual_slip = _f(trade, "slippage_paid", float("nan"))
    if actual_slip == actual_slip:
        side = _outside(actual_slip, expected_slip, rel_tol)
        if side == "high":
            issues.append(
                FeeIssue(
                    "SLIPPAGE_MULTIPLE",
                    tid,
                    f"slippage {actual_slip:.4f} > one-pass expectation "
                    f"{expected_slip:.4f} -- slippage looks double-counted",
                    expected_slip,
                    actual_slip,
                )
            )

    return issues


def check_trades(
    trades: Sequence[dict],
    fee_bps: float = DEFAULT_RATES["fee_bps"],
    funding_bps_per_bar: float = DEFAULT_RATES["funding_bps_per_bar"],
    slippage_bps: float = DEFAULT_RATES["slippage_bps"],
    rel_tol: float = REL_TOL,
) -> List[FeeIssue]:
    out: List[FeeIssue] = []
    for trade in trades:
        out.extend(
            check_trade(trade, fee_bps, funding_bps_per_bar, slippage_bps, rel_tol)
        )
    return out
