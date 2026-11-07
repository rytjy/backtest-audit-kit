"""Metric definitions that are easy to get subtly wrong.

Two failure modes this module catches:

* Sortino downside deviation divided by the number of losing periods
  instead of all observations. The denominator is then inflated by
  sqrt(N / K) (K = losing periods), so the reported Sortino is
  understated by sqrt(K / N).
* Funding dropped at the exit boundary: a funding event falling exactly
  on a position's exit timestamp is skipped when the engine advances the
  funding cursor after closing the position.

Returns are decimal returns (0.01 = 1%). Rates are decimal, not bp.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

__all__ = [
    "MetricIssue",
    "downside_deviation",
    "sortino_ratio",
    "check_reported_sortino",
    "check_funding_coverage",
]


@dataclass(frozen=True)
class MetricIssue:
    rule: str
    message: str
    expected: Optional[float] = None
    actual: Optional[float] = None

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
        }

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"[{self.rule}] {self.message}"


def downside_deviation(returns: Sequence[float], target: float = 0.0) -> float:
    """Root mean square of min(r - target, 0) over ALL observations."""
    if not returns:
        return 0.0
    ss = sum(min(r - target, 0.0) ** 2 for r in returns)
    return math.sqrt(ss / len(returns))


def _wrong_downside(returns: Sequence[float], target: float = 0.0) -> float:
    """The common mistake: RMS over losing periods only."""
    downs = [r - target for r in returns if r - target < 0.0]
    if not downs:
        return 0.0
    return math.sqrt(sum(d * d for d in downs) / len(downs))


def sortino_ratio(
    returns: Sequence[float],
    annualization_factor: float,
    risk_free: float = 0.0,
) -> Optional[float]:
    """Annualised Sortino with the standard downside deviation.

    risk_free is an annual rate; it is de-annualised by
    annualization_factor before subtraction, matching the usual
    daily-excess-return convention.
    """
    if len(returns) < 2:
        return None
    rf_per_period = risk_free / annualization_factor
    excess = [r - rf_per_period for r in returns]
    dd = downside_deviation(excess)
    if dd == 0.0:
        return None
    mean = sum(excess) / len(excess)
    return mean / dd * math.sqrt(annualization_factor)


def check_reported_sortino(
    reported: float,
    returns: Sequence[float],
    annualization_factor: float,
    risk_free: float = 0.0,
    rel_tol: float = 0.02,
) -> list[MetricIssue]:
    """Compare a reported Sortino with both the correct and the common wrong one.

    If the reported value matches the wrong denominator variant but not the
    correct one, the rule is SORTINO_DOWNSIDE_DENOMINATOR. Any other
    material gap is SORTINO_MISMATCH.
    """
    correct = sortino_ratio(returns, annualization_factor, risk_free)
    if correct is None:
        return []
    rf_per_period = risk_free / annualization_factor
    excess = [r - rf_per_period for r in returns]
    mean = sum(excess) / len(excess)
    wrong_dd = _wrong_downside(excess)
    wrong = None if wrong_dd == 0.0 else mean / wrong_dd * math.sqrt(annualization_factor)

    def close(a: float, b: Optional[float]) -> bool:
        if b is None or b == 0.0:
            return False
        return abs(a - b) / abs(b) <= rel_tol

    if close(reported, correct):
        return []
    if wrong is not None and close(reported, wrong):
        return [
            MetricIssue(
                "SORTINO_DOWNSIDE_DENOMINATOR",
                "downside deviation divided by losing periods, not all observations",
                expected=correct,
                actual=reported,
            )
        ]
    return [
        MetricIssue(
            "SORTINO_MISMATCH",
            "reported Sortino differs from the recomputed one",
            expected=correct,
            actual=reported,
        )
    ]


def check_funding_coverage(
    trades: Iterable[dict],
    funding_events: Iterable[dict],
    abs_tol: float = 1e-6,
) -> list[MetricIssue]:
    """Check that funding inside each holding window was actually charged.

    trades need entry_time, exit_time and funding_paid.
    funding_events need time and payment (signed; negative = paid).

    An event at exactly exit_time belongs to the holding window: the
    position was still open when it was due. Engines that advance the
    funding cursor after closing the position drop exactly that event.
    """
    events = list(funding_events)
    issues: list[MetricIssue] = []
    for trade in trades:
        entry = trade.get("entry_time")
        exit_ = trade.get("exit_time")
        if entry is None or exit_ is None:
            continue
        actual = trade.get("funding_paid")
        if actual is None:
            continue
        expected = sum(
            float(e["payment"])
            for e in events
            if entry < float(e["time"]) <= exit_
        )
        if abs(expected - float(actual)) > abs_tol:
            boundary = any(
                abs(float(e["time"]) - float(exit_)) <= abs_tol for e in events
            )
            rule = "FUNDING_GAP_AT_EXIT" if boundary else "FUNDING_GAP"
            issues.append(
                MetricIssue(
                    rule,
                    f"funding inside holding window {entry}..{exit_} not fully charged",
                    expected=expected,
                    actual=float(actual),
                )
            )
    return issues
