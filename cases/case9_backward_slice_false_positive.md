# Case 9 — Our own look-ahead checker flagged a backward window

> **Status: fixed 2026-10-28.** The false positive below was found by auditing
> ourselves, reported here, and repaired in `auditkit/checks/lookahead.py` with a
> regression test. Numbers in "Measured on a corpus" are pre-fix.

**Symptom.** A rolling window that ends *today* was reported as a future leak:

```python
for i in range(n, len(c)):
    w = c[i-n+1:i+1]        # ends at i — no future data
    out.append(sum(w)/len(w))
```

`detect()` returned **HIGH / FUTURE_SLICE**. Removing only the `+1` — `c[i-n:i]` —
returned **nothing**. One character flipped the verdict.

**Root cause.** `_adds_positive_int` tested both operands of `Add` independently:

```python
if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
    return _is_positive_int(node.right) or _is_positive_int(node.left)
```

For the lower bound `(i - n) + 1` the right operand is `1`, so the helper answered
"anchor plus a positive constant" without asking which way the anchor moves.
Severity was then raised to `HIGH` inside any loop (`loop_depth >= 1`) — exactly
where rolling windows live.

**Measured on a corpus we control (pre-fix).** Scanning our own workspace: of the
**54** `FUTURE_SLICE` findings, **18** were this backward shape, including **4 in
our own indicator library**.

**Why a false HIGH is worse than a miss.** A miss leaves the client where they
were. A false HIGH in a paid report teaches them the checker cries wolf — and the
internal version of the same failure happened: with hundreds of alerts across the
codebase, nobody opened them. A linter's false-positive rate is a product feature.

**The fix.** Replace the two-sided test with a net-offset computation:

```python
def _anchor_offset(node):      # i + 1 -> 1 ; i - 24 -> -24 ; (i - n) + 1 -> None
    ...
def _adds_positive_int(node):
    offset = _anchor_offset(node)
    return offset is not None and offset > 0
```

A chain is "provably forward" only when it resolves to `anchor + k`, `k > 0`. If an
unknown amount is subtracted from the anchor, the result is `None` — the checker
stays quiet rather than guessing. `(i - 3) + 5` still resolves to `+2` and is still
reported.

**A/B on the same 754-file corpus, old vs new:**

| | findings | HIGH | MEDIUM | `FUTURE_SLICE` |
|---|---:|---:|---:|---:|
| before | 450 | 106 | 344 | 54 |
| after | **427** | **95** | **332** | **36** |

23 findings disappear; the 18 slice false positives are the bulk of it. The
repository suite (6 tests, including a new regression that asserts the backward
window is clean *and* that `c[i+1:i+5]` and `c[(i-3)+5:]` are still caught) passes.

**Bottom line.** Before selling a linter, measure it on a corpus whose labels you
know. Ours was measured by accident, while auditing ourselves — 18 of 54 slice
findings were wrong, and the repair cost one afternoon.

**Caveats.** Still a heuristic linter, not a proof engine. The 18 were classified
by hand among the 54; the remaining 36 slice findings were not re-reviewed, and
other false-positive shapes may remain. Corpus numbers come from one workspace
snapshot, not a benchmark.
