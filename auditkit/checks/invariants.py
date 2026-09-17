"""Ledger invariants.

A backtest is an accounting system; accounting systems have invariants.  When a
result looks impossible it is usually because one of these was violated
somewhere in the loop, and the bug silently reshaped the equity curve.

The checker consumes a ``ledger``: an ordered list of per-step ``dict`` records.
Only the keys you provide are checked; the canonical ones are:

===============  ==========================================================
key              meaning
===============  ==========================================================
``step``/``bar`` optional step label (used in messages)
``cap``          total equity (cash + market value of open positions)
``cash``         free cash (excludes position value)
``positions``    ``{symbol: market_value}``
``wd``           amount withdrawn on this step (default ``0``)
``wd_cum``       cumulative withdrawals to date
``bust``         ``True`` if this step returned via the liquidation path
``trades``       counter, must be non-decreasing (also ``n_events``, ``bars``,
                 ``fills``)
===============  ==========================================================

Rules
-----
``EQUITY_IDENTITY``    ``cap == cash + sum(positions.values())`` within tolerance.
``NEGATIVE_BALANCE``   ``cap`` / ``cash`` / ``equity`` never below zero.
``NEGATIVE_POSITION``  no negative position values.
``WD_MONOTONIC``       ``wd_cum`` is non-decreasing.
``WD_ACCRUAL``         withdrawing ``wd`` must grow ``wd_cum`` by exactly ``wd``.
``BUST_WD_CARRY``      the liquidation/bust path must *carry* ``wd_cum`` forward,
                       not reset it (the bug that erased history in case 2/3).
``COUNTER_MONOTONIC``  counters never decrease.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

__all__ = ["Violation", "check_ledger", "DEFAULT_COUNTERS", "DEFAULT_TOL"]

DEFAULT_TOL = 1e-6
DEFAULT_COUNTERS: Sequence[str] = ("trades", "n_events", "bars", "fills")
_BALANCE_KEYS = ("cap", "cash", "equity")


@dataclass(frozen=True)
class Violation:
    rule: str
    step: object
    message: str

    def as_dict(self) -> dict:
        return {"rule": self.rule, "step": self.step, "message": self.message}

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"[{self.rule}] step={self.step}: {self.message}"


def _num(rec: dict, key: str, default: float = 0.0) -> float:
    val = rec.get(key, default)
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _step(rec: dict, fallback: int) -> object:
    return rec.get("step", rec.get("bar", fallback))


def check_ledger(
    ledger: Sequence[dict],
    tol: float = DEFAULT_TOL,
    counters: Iterable[str] = DEFAULT_COUNTERS,
) -> List[Violation]:
    """Run every invariant over ``ledger`` and return all violations found."""
    violations: List[Violation] = []
    counters = tuple(counters)
    prev: Optional[dict] = None

    for idx, rec in enumerate(ledger):
        step = _step(rec, idx)

        # --- equity identity -------------------------------------------- #
        if "cap" in rec and "cash" in rec:
            pos = rec.get("positions") or {}
            pos_value = sum(_num({"v": v}, "v") for v in pos.values())
            diff = _num(rec, "cap") - (_num(rec, "cash") + pos_value)
            if abs(diff) > tol:
                violations.append(
                    Violation(
                        "EQUITY_IDENTITY",
                        step,
                        f"cap={_num(rec, 'cap'):.6f} but cash+positions="
                        f"{_num(rec, 'cash') + pos_value:.6f} (diff {diff:+.6f})",
                    )
                )

        # --- non-negative balances -------------------------------------- #
        for key in _BALANCE_KEYS:
            if key in rec and _num(rec, key) < -tol:
                violations.append(
                    Violation("NEGATIVE_BALANCE", step, f"{key}={_num(rec, key):.6f} < 0")
                )
        for sym, val in (rec.get("positions") or {}).items():
            if _num({"v": val}, "v") < -tol:
                violations.append(
                    Violation(
                        "NEGATIVE_POSITION", step, f"position {sym}={val} < 0"
                    )
                )

        if prev is not None:
            # --- wd_cum ----------------------------------------------- #
            if "wd_cum" in rec and "wd_cum" in prev:
                wd_cum, prev_wd_cum = _num(rec, "wd_cum"), _num(prev, "wd_cum")
                if wd_cum < prev_wd_cum - tol:
                    violations.append(
                        Violation(
                            "WD_MONOTONIC",
                            step,
                            f"wd_cum decreased {prev_wd_cum:.6f} -> {wd_cum:.6f}",
                        )
                    )
                wd = _num(rec, "wd", 0.0)
                if wd > tol:
                    grew = wd_cum - prev_wd_cum
                    if abs(grew - wd) > tol:
                        violations.append(
                            Violation(
                                "WD_ACCRUAL",
                                step,
                                f"withdrew {wd:.6f} but wd_cum grew {grew:+.6f}",
                            )
                        )

            # --- bust must carry wd_cum ------------------------------- #
            if rec.get("bust"):
                if "wd_cum" in prev and _num(prev, "wd_cum") > tol:
                    if "wd_cum" not in rec:
                        violations.append(
                            Violation(
                                "BUST_WD_CARRY",
                                step,
                                "bust path returned cap without wd_cum "
                                f"(prev wd_cum={_num(prev, 'wd_cum'):.6f})",
                            )
                        )
                    elif _num(rec, "wd_cum") < _num(prev, "wd_cum") - tol:
                        violations.append(
                            Violation(
                                "BUST_WD_CARRY",
                                step,
                                "bust path dropped wd_cum "
                                f"{_num(prev, 'wd_cum'):.6f} -> {_num(rec, 'wd_cum'):.6f}",
                            )
                        )

            # --- counters --------------------------------------------- #
            for c in counters:
                if c in rec and c in prev and _num(rec, c) < _num(prev, c) - tol:
                    violations.append(
                        Violation(
                            "COUNTER_MONOTONIC",
                            step,
                            f"{c} decreased {_num(prev, c):g} -> {_num(rec, c):g}",
                        )
                    )

        prev = rec

    return violations


def violations_by_rule(violations: Sequence[Violation]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for v in violations:
        out[v.rule] = out.get(v.rule, 0) + 1
    return out
