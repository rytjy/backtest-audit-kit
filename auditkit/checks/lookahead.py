"""Look-ahead / future-function detection.

A *look-ahead* (a.k.a. future leak) is code that lets a strategy decision on
bar ``i`` see information that only exists on bars ``i+1...``.  In a backtest
this silently inflates results, and it is the single most common reason a
"profitable" strategy dies in production.

This module is a *heuristic linter*, not a proof engine.  It parses source with
``ast`` and flags three shapes that are strongly correlated with future leaks:

``NEGATIVE_SHIFT``
    ``series.shift(-1)`` / ``pct_change(-1)`` / ``diff(-1)`` — pulls the next
    value into the current row.  Positive shifts read the past and are fine.

``FUTURE_SLICE`` / ``FUTURE_INDEX``
    ``data[i + 1:]`` (open-ended future slice) or ``data[i + 1]`` (direct read
    of the next bar), where the lower bound is an anchor plus a positive
    constant.

``FUTURE_WINDOW_LOOP``
    ``for j in range(ei + 1, min(ei + 1 + TO, n)):`` — a forward window scan.
    When such a loop is *nested inside* another bar loop it is the classic
    "decide the exit on the entry bar" bug and is reported ``HIGH``.  A
    stand-alone forward loop is reported ``MEDIUM`` for manual review, because
    a correctly written simulation pass also walks forward (see note below).

Design note / honest limitation
-------------------------------
Statics cannot tell a *simulation* pass from a *decision* leak.  The fixed
version of case 1 avoids the ambiguity entirely by evaluating the exit **only
on the current bar** while the backtest advances, so it produces zero findings.
If you do keep a separate forward simulation pass, expect a ``MEDIUM`` finding;
that is intentional and means "a human should confirm this pass cannot feed
back into the entry decision".
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

__all__ = [
    "Finding",
    "LookaheadDetector",
    "detect",
    "detect_file",
    "format_findings",
    "SEVERITY_ORDER",
]

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

#: Methods that reach into the future when called with a negative argument.
FUTURE_METHODS = frozenset({"shift", "pct_change", "diff"})


@dataclass(frozen=True)
class Finding:
    """One suspicious construct found in the source."""

    rule: str
    severity: str
    lineno: int
    message: str
    snippet: str = ""

    def as_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "lineno": self.lineno,
            "message": self.message,
            "snippet": self.snippet,
        }

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"[{self.severity}] {self.rule} L{self.lineno}: {self.message}"


# --------------------------------------------------------------------------- #
# small AST helpers
# --------------------------------------------------------------------------- #
def _is_int_const(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _is_positive_int(node: ast.AST) -> bool:
    return _is_int_const(node) and node.value > 0  # type: ignore[attr-defined]


def _is_negative_int(node: ast.AST) -> bool:
    if _is_int_const(node) and node.value < 0:  # type: ignore[attr-defined]
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return _is_positive_int(node.operand)
    return False


def _adds_positive_int(node: ast.AST) -> bool:
    """True iff ``node`` looks like ``<anchor> + k`` with ``k`` a positive int.

    A bare constant is *not* a match, so ``range(1, n)`` stays clean.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _is_positive_int(node.right) or _is_positive_int(node.left)
    return False


def _is_range_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
    )


def _call_name(node: ast.Call) -> Optional[str]:
    fn = node.func
    if isinstance(fn, ast.Attribute):
        return fn.attr
    if isinstance(fn, ast.Name):
        return fn.id
    return None


# --------------------------------------------------------------------------- #
# visitor
# --------------------------------------------------------------------------- #
class LookaheadDetector(ast.NodeVisitor):
    """Walk a parsed module and collect :class:`Finding` objects."""

    def __init__(self) -> None:
        self.findings: List[Finding] = []
        self._loop_depth = 0  # number of enclosing ``for ... in range(...)`` loops

    # -- loops -------------------------------------------------------------- #
    def visit_For(self, node: ast.For) -> None:  # noqa: N802 (ast API)
        if _is_range_call(node.iter):
            self._check_range(node, node.iter)  # type: ignore[arg-type]
            self._loop_depth += 1
            self.generic_visit(node)
            self._loop_depth -= 1
        else:
            self.generic_visit(node)

    def _check_range(self, loop: ast.For, call: ast.Call) -> None:
        if len(call.args) < 2:
            return
        start = call.args[0]
        if not _adds_positive_int(start):
            return
        severity = "HIGH" if self._loop_depth >= 1 else "MEDIUM"
        target = _target_name(loop.target)
        self.findings.append(
            Finding(
                rule="FUTURE_WINDOW_LOOP",
                severity=severity,
                lineno=loop.lineno,
                message=(
                    f"forward window scan `range({ast.unparse(start)}, ...)` over "
                    f"`{target}` starts strictly after an anchor; "
                    + (
                        "nested inside another bar loop -> looks like the exit is "
                        "decided on the entry bar"
                        if severity == "HIGH"
                        else "stand-alone forward pass -- confirm it cannot feed the entry decision"
                    )
                ),
                snippet=ast.unparse(call),
            )
        )

    # -- calls -------------------------------------------------------------- #
    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        name = _call_name(node)
        if name in FUTURE_METHODS and node.args and _is_negative_int(node.args[0]):
            self.findings.append(
                Finding(
                    rule="NEGATIVE_SHIFT",
                    severity="HIGH",
                    lineno=node.lineno,
                    message=(
                        f"`{name}({ast.unparse(node.args[0])})` reads the future "
                        "(positive lag reads the past)"
                    ),
                    snippet=ast.unparse(node),
                )
            )
        self.generic_visit(node)

    # -- indexing ----------------------------------------------------------- #
    def visit_Subscript(self, node: ast.Subscript) -> None:  # noqa: N802
        sl = node.slice
        if isinstance(sl, ast.Slice):
            if sl.lower is not None and _adds_positive_int(sl.lower):
                self.findings.append(
                    Finding(
                        rule="FUTURE_SLICE",
                        severity="HIGH" if self._loop_depth >= 1 else "MEDIUM",
                        lineno=node.lineno,
                        message=(
                            "slice lower bound is an anchor plus a positive "
                            "constant -> the slice reaches into the future"
                        ),
                        snippet=ast.unparse(node),
                    )
                )
        elif _adds_positive_int(sl):
            self.findings.append(
                Finding(
                    rule="FUTURE_INDEX",
                    severity="MEDIUM",
                    lineno=node.lineno,
                    message="direct index of the next bar (anchor + positive constant)",
                    snippet=ast.unparse(node),
                )
            )
        self.generic_visit(node)


def _target_name(target: ast.AST) -> str:
    if isinstance(target, ast.Name):
        return target.id
    return ast.unparse(target)


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #
def detect(source: str, filename: str = "<string>") -> List[Finding]:
    """Return all findings for ``source``, sorted by line number."""
    tree = ast.parse(source, filename=filename)
    visitor = LookaheadDetector()
    visitor.visit(tree)
    return sorted(visitor.findings, key=lambda f: (f.lineno, f.rule))


def detect_file(path: str | Path) -> List[Finding]:
    p = Path(path)
    return detect(p.read_text(encoding="utf-8"), filename=str(p))


def format_findings(findings: Sequence[Finding]) -> str:
    if not findings:
        return "clean: no look-ahead patterns detected"
    return "\n".join(str(f) for f in findings)
