"""Mutation testing: which bugs would your tests *not* catch?

Your backtest engine has a test suite.  It passes.  That proves very little:
tests pass on code that is wrong in a way the tests never probe.  Mutation
testing measures that gap mechanically.

For a target function we generate *mutants* — single, small, semantically real
changes (flip a comparator, off-by-one a constant, swap non-commutative
operands, delete a fee/commission term).  Each mutant is executed against your
suite.  If the suite still passes, the mutant **survived** — that mutation is a
coverage blind spot, and the same blind spot will happily hide a real bug.

Public API
----------
``generate_mutants(source)`` -> ``list[Mutant]``
``run_mutation_tests(source, test_suite)`` -> ``MutationResult``

A ``test_suite`` is a callable ``(namespace: dict) -> None`` where
``namespace`` is the module-level globals of the (mutated) target module.  It
should raise (e.g. ``assert``) when the behaviour is wrong, and return quietly
otherwise.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Tuple

__all__ = [
    "Mutant",
    "MutationResult",
    "generate_mutants",
    "run_mutation_tests",
    "DEFAULT_KINDS",
    "COMPARE_FLIP",
    "FEE_WORDS",
]

DEFAULT_KINDS = ("compare", "offbyone", "swap", "delete_fee")

COMPARE_FLIP = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}

#: Only non-commutative operators are worth swapping (``a+b == b+a``).
SWAP_OPS = (ast.Sub, ast.Div)

FEE_WORDS = ("fee", "commission", "funding", "slip", "borrow", "cost")

TestSuite = Callable[[Dict[str, object]], None]


@dataclass(frozen=True)
class Mutant:
    id: str
    kind: str
    description: str
    source: str


@dataclass
class MutationResult:
    total: int
    killed: int
    survived: List[Mutant]
    score: float
    details: List[Tuple[str, str, str]] = field(default_factory=list)

    @property
    def survivors(self) -> List[Mutant]:
        return self.survived

    def report(self) -> str:
        lines = [
            f"mutants generated : {self.total}",
            f"killed            : {self.killed}",
            f"survived          : {len(self.survived)}",
            f"mutation score    : {self.score * 100:.1f}%",
        ]
        if self.survived:
            lines.append("blind spots (surviving mutants):")
            for m in self.survived:
                lines.append(f"  - [{m.id}] {m.description}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# source-level mutation
# --------------------------------------------------------------------------- #
def _walk_deterministic(tree: ast.AST) -> List[ast.AST]:
    return list(ast.walk(tree))


def _apply_nth(source: str, predicate, mutate, index: int) -> str:
    """Re-parse ``source``, mutate the ``index``-th node matching ``predicate``."""
    tree = ast.parse(source)
    seen = 0
    for node in _walk_deterministic(tree):
        if predicate(node):
            if seen == index:
                mutate(node)
                ast.fix_missing_locations(tree)
                return ast.unparse(tree)
            seen += 1
    raise IndexError(f"no node #{index} matched predicate")


def _compare_pred(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and type(node.ops[0]) in COMPARE_FLIP
    )


def _offbyone_pred(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _swap_pred(node: ast.AST) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, SWAP_OPS)


def _stmt_has_fee_word(stmt: ast.stmt) -> bool:
    for node in ast.walk(stmt):
        name = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        if name and any(w in name.lower() for w in FEE_WORDS):
            return True
    return False


def _fee_stmts(tree: ast.AST) -> List[ast.stmt]:
    """Statements that directly live in a function/module body and mention a fee.

    Entire function/class definitions are never candidates -- deleting a whole
    function is not a realistic "forgot the fee" edit.
    """
    out: List[ast.stmt] = []
    for node in _walk_deterministic(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            for stmt in node.body:
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if _stmt_has_fee_word(stmt):
                    out.append(stmt)
    return out


def _delete_nth_fee_stmt(source: str, index: int) -> str:
    tree = ast.parse(source)
    targets = _fee_stmts(tree)
    if index >= len(targets):
        raise IndexError("no such fee statement")
    fingerprint = ast.unparse(targets[index])

    class _Deleter(ast.NodeTransformer):
        def __init__(self) -> None:
            self.done = False

        def generic_visit(self, node: ast.AST) -> ast.AST:
            if not self.done:
                for attr in ("body", "orelse", "finalbody"):
                    body = getattr(node, attr, None)
                    if isinstance(body, list):
                        for i, stmt in enumerate(body):
                            if isinstance(stmt, ast.stmt) and ast.unparse(stmt) == fingerprint:
                                del body[i]
                                self.done = True
                                break
            return super().generic_visit(node)

    _Deleter().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def generate_mutants(
    source: str, kinds: Optional[Iterable[str]] = None
) -> List[Mutant]:
    """Generate first-order mutants for ``source``."""
    kinds = tuple(kinds) if kinds is not None else DEFAULT_KINDS
    kindset = set(kinds)
    base = ast.parse(source)
    mutants: List[Mutant] = []

    if "compare" in kindset:
        for i, node in enumerate(
            [n for n in _walk_deterministic(base) if _compare_pred(n)]
        ):
            old, new = type(node.ops[0]), COMPARE_FLIP[type(node.ops[0])]
            mid = f"cmp{i}"

            def _mutate(n, old=old, new=new):
                n.ops[0] = new()

            mutants.append(
                Mutant(
                    mid,
                    "compare",
                    f"flip `{old.__name__}` -> `{new.__name__}` at L{node.lineno}",
                    _apply_nth(source, _compare_pred, _mutate, i),
                )
            )

    if "offbyone" in kindset:
        for i, node in enumerate(
            [n for n in _walk_deterministic(base) if _offbyone_pred(n)]
        ):
            for delta, tag in ((1, "up"), (-1, "down")):
                mid = f"ob{tag}{i}"

                def _mutate(n, delta=delta):
                    n.value = n.value + delta

                mutants.append(
                    Mutant(
                        mid,
                        "offbyone",
                        f"constant {node.value} -> {node.value + delta} at L{node.lineno}",
                        _apply_nth(source, _offbyone_pred, _mutate, i),
                    )
                )

    if "swap" in kindset:
        for i, node in enumerate(
            [n for n in _walk_deterministic(base) if _swap_pred(n)]
        ):
            mid = f"swap{i}"

            def _mutate(n):
                n.left, n.right = n.right, n.left

            mutants.append(
                Mutant(
                    mid,
                    "swap",
                    f"swap operands of `{type(node.op).__name__}` at L{node.lineno}",
                    _apply_nth(source, _swap_pred, _mutate, i),
                )
            )

    if "delete_fee" in kindset:
        for i, stmt in enumerate(_fee_stmts(base)):
            mid = f"delfee{i}"
            mutants.append(
                Mutant(
                    mid,
                    "delete_fee",
                    f"delete fee/cost statement `{ast.unparse(stmt)}` at L{stmt.lineno}",
                    _delete_nth_fee_stmt(source, i),
                )
            )

    # de-duplicate identical sources (e.g. equivalent flips)
    seen: set = set()
    unique: List[Mutant] = []
    for m in mutants:
        if m.source in seen:
            continue
        seen.add(m.source)
        unique.append(m)
    return unique


# --------------------------------------------------------------------------- #
# execution
# --------------------------------------------------------------------------- #
def run_mutation_tests(
    source: str,
    test_suite: TestSuite,
    name: str = "target",
    kinds: Optional[Iterable[str]] = None,
) -> MutationResult:
    """Run ``test_suite`` against every mutant of ``source``."""
    mutants = generate_mutants(source, kinds)
    survived: List[Mutant] = []
    details: List[Tuple[str, str, str]] = []
    killed = 0

    for mutant in mutants:
        try:
            namespace: Dict[str, object] = {
                "__name__": f"auditkit_mutant_{mutant.id}",
                "__builtins__": __builtins__,
            }
            exec(compile(mutant.source, f"<{name}:{mutant.id}>", "exec"), namespace)
        except Exception as exc:  # mutant does not even import -> killed
            killed += 1
            details.append((mutant.id, "killed", f"load failed: {exc!r}"))
            continue

        try:
            test_suite(namespace)
        except Exception as exc:
            killed += 1
            details.append((mutant.id, "killed", f"{type(exc).__name__}: {exc}"))
        else:
            survived.append(mutant)
            details.append((mutant.id, "survived", mutant.description))

    total = len(mutants)
    score = killed / total if total else 1.0
    return MutationResult(total, killed, survived, score, details)
