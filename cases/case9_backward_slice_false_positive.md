# Case 9 — Our own look-ahead checker flags a backward window

**Symptom.** A rolling window that ends *today* is reported as a future leak:

```python
for i in range(n, len(c)):
    w = c[i-n+1:i+1]        # ends at i — no future data
    out.append(sum(w)/len(w))
```

Running `detect()` on that file returns **HIGH / FUTURE_SLICE**. Removing only
the `+1` — `c[i-n:i]` — returns **nothing**. One character flips the verdict.

**Root cause.** `auditkit/checks/lookahead.py`, `_adds_positive_int`:

```python
if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
    return _is_positive_int(node.right) or _is_positive_int(node.left)
```

For the lower bound `(i - n) + 1` the right operand is `1`, so the helper
answers "anchor plus a positive constant" — without asking which direction the
anchor itself moves. Severity is then raised to `HIGH` whenever the slice sits
inside a loop (`loop_depth >= 1`), which is exactly where rolling windows live.

**Measured on a corpus we control.** Scanning 583 `.py` files in our own
workspace: 438 findings (HIGH 106 / MEDIUM 332). Of the **54** `FUTURE_SLICE`
findings, **18 are this backward shape**, including **4 in our own indicator
library** (`ci_lib.py`).

**Why a false HIGH is worse than a miss.** A miss leaves the client where they
were. A false HIGH in a paid report teaches them that the checker cries wolf —
and they stop reading. Internally the same thing happened at scale: with 438
alerts across the codebase, we stopped opening them. The tool's own
false-positive rate is a product feature, not an implementation detail.

**Fix direction** (not yet applied at HEAD). Before accepting `anchor + k`, look
at the *other* operand: if it is itself `i - j` with `j >= k`, the window still
ends at or before `i` and must not be reported. `c[(i-n)+1:i+1]` is the same
window as `c[i-n+1:i+1]` and needs the same treatment.

**Bottom line.** Before selling a linter, measure it on a corpus whose labels you
know. Ours was measured — by accident, while auditing ourselves — and 18 of 54
slice findings were wrong.

**Caveats.** This is a heuristic linter, not a proof engine: a genuinely
forward-looking slice can look like a backward one and vice versa. The 18 were
classified by hand among the 54 `FUTURE_SLICE` findings; the other 36 were not
re-checked, and other false-positive shapes may remain. Numbers are from one
snapshot of one workspace, not a benchmark corpus.
