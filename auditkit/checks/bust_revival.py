"""Bust-revival detection.

A *bust revival* is code that, after declaring an account ruined
("if cap <= 0"), resets the account to a tiny positive constant
("cap = 0.01") and keeps compounding.  The backtest then reports a
survivor that never existed: in a leveraged path the losing trade is
supposed to end the account, not hand it 1% of the starting capital.

Two shapes are flagged:

REVIVAL_ASSIGN (HIGH)
    if cap <= 0: cap = 0.01 -- an explicit reset inside a ruin check.
    HIGH when the variable is compounded (multiplied) in the same
    function; MEDIUM when it is not.

REVIVAL_CLAMP (MEDIUM)
    cap = max(cap * (1 + r), 0.01) -- a floor applied on every step.
    A floor of 1e-9 is a division guard and is not flagged; the
threshold is 0.1 so only percent-scale revivals match.

This is a heuristic linter.  It cannot tell a deliberate unit floor from a
ruin reset; it points a human at the line.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

__all__ = ["Finding", "detect", "detect_file", "format_findings", "SEVERITY_ORDER"]

SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
REVIVAL_MAX = 0.1  # constants above this are units, not 1% revivals
RUIN_OPS = (ast.LtE, ast.Lt, ast.Eq)


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    lineno: int
    message: str
    snippet: str

    def __str__(self) -> str:
        return f"{self.severity:6s} L{self.lineno:<5d} {self.rule:14s} {self.message}  |  {self.snippet}"


def _const(node: ast.AST) -> Optional[float]:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    return None


def _ruin_name(test: ast.AST) -> Optional[str]:
    """Return the variable compared against ~zero in a ruin check."""
    if not isinstance(test, ast.Compare):
        return None
    if not any(isinstance(op, RUIN_OPS) for op in test.ops):
        return None
    names = [n.id for n in [test.left, *test.comparators] if isinstance(n, ast.Name)]
    consts = [_const(c) for c in test.comparators]
    if not names:
        return None
    if any(c is not None and 0 <= c <= 0.1 for c in consts):
        return names[0]
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.findings: List[Finding] = []
        self._loop_depth = 0
        self._func_stack: List[set] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        compounded = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Mult):
                for side in (sub.left, sub.right):
                    if isinstance(side, ast.Name):
                        compounded.add(side.id)
        self._func_stack.append(compounded)
        self.generic_visit(node)
        self._func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_For(self, node: ast.For) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    visit_While = visit_For

    def _compounded(self, name: str) -> bool:
        return bool(self._func_stack) and name in self._func_stack[-1]

    def visit_If(self, node: ast.If) -> None:
        name = _ruin_name(node.test)
        if name:
            for stmt in node.body:
                c = None
                if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in stmt.targets):
                    c = _const(stmt.value)
                elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name) and stmt.target.id == name:
                    c = _const(stmt.value)
                if c is not None and 0 < c <= REVIVAL_MAX:
                    sev = "HIGH" if (self._loop_depth > 0 and self._compounded(name)) else "MEDIUM"
                    self.findings.append(Finding(
                        rule="REVIVAL_ASSIGN", severity=sev, lineno=stmt.lineno,
                        message=f"ruin check resets {name!r} to {c:g} and keeps trading",
                        snippet=ast.unparse(stmt)))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "max":
            args = node.value.args
            if len(args) >= 2:
                c = _const(args[-1])
                target = node.targets[0]
                if c is not None and 0 < c <= REVIVAL_MAX and isinstance(target, ast.Name):
                    sev = "HIGH" if (self._loop_depth > 0 and self._compounded(target.id)) else "MEDIUM"
                    self.findings.append(Finding(
                        rule="REVIVAL_CLAMP", severity=sev, lineno=node.lineno,
                        message=f"{target.id!r} is floored at {c:g} on every step",
                        snippet=ast.unparse(node)))
        self.generic_visit(node)


def detect(source: str, filename: str = "<string>") -> List[Finding]:
    tree = ast.parse(source, filename=filename)
    v = _Visitor()
    v.visit(tree)
    return sorted(v.findings, key=lambda f: (f.lineno, f.rule))


def detect_file(path: str | Path) -> List[Finding]:
    p = Path(path)
    return detect(p.read_text(encoding="utf-8"), filename=str(p))


def format_findings(findings: Sequence[Finding]) -> str:
    if not findings:
        return "clean: no bust-revival patterns detected"
    return "\n".join(str(f) for f in findings)
