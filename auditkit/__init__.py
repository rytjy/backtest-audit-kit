"""auditkit — a tiny, dependency-free toolkit for auditing backtests.

The toolkit answers one question: *is this strategy real, or did the backtest
lie to you?*  It ships four independent checkers:

* ``auditkit.checks.lookahead``   — AST-based look-ahead / future-function lint.
* ``auditkit.checks.invariants``  — ledger invariants (equity identity, wd_cum, monotonic counters).
* ``auditkit.checks.mutants``     — mutation testing: which bugs would your tests *not* catch?
* ``auditkit.checks.fees``        — fee / funding / slippage accounting checks.

Everything is pure standard library (Python 3.9+).  No pandas, no numpy,
no network access.
"""

__version__ = "0.1.0"
__all__ = ["checks"]
