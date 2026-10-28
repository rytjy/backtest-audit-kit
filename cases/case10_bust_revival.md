# Case 10 — the account that comes back from the dead

> Scope: this case is about a *simulation* bug, not a market claim. It shows how a
> one-line ruin guard turns a wiped account into a survivor, and how to detect the
> shape statically. Reproduce with `auditkit/checks/bust_revival.py`.

## The shape

```python
cap = 1.0
for r in returns:
    cap *= (1 + lev * r)
    if cap <= 0:
        cap = 0.01          # <-- the account is revived at 1% and keeps trading
```

A leveraged path that loses more than the margin is *over*. Resetting the balance to
1% of the starting capital does two things at once:

1. it makes the bust invisible in the equity curve (the account simply continues), and
2. it lets later winners compound from a fresh stake, which the real account never had.

The same bug appears as a floor: `cap = max(cap * (1 + r), 0.01)`.

## What it did to one of our own engines

`bt_withdraw_design.py` (5x, 487 events, forward 24h returns rebuilt after the
column-semantics bug in case 8). With the revival floor kept, the withdrawal rules
looked like this (median total wealth, 216 year-block permutations):

| rule | with `cap = 0.01` floor | with "stop when ruined" |
|---|---:|---:|
| A no withdrawal | 0.2x | 0.00x (99.5% bust at K=1) |
| B withdraw 1x at 2x | 23.0x | 1.00x |
| C1 withdraw above 2x | 32.2x | 0.17x |
| C2 above 3x | 42.9x | 0.00x |
| C3 above 5x | 64.9x | 0.00x |
| C4 above 10x | 116.8x | 0.00x |
| D ladder 2/4/8 | 25.2x | 1.09x |

The left column is the bug. The right column is the same rules with a single change:
a wiped position loses its margin and the account stops. At 5x with intrabar
liquidation, K=1..5 busts in 42–99.5% of paths; only a 1/10-sized book (K=10) survives.

## Detection

`bust_revival` parses with `ast` and flags two shapes:

- `REVIVAL_ASSIGN` — an assignment to a small positive constant inside an `if` that
  compares the same variable to zero. `HIGH` when the variable is multiplied
  (compounded) in the same function, otherwise `MEDIUM`.
- `REVIVAL_CLAMP` — `x = max(expr, 0.01)`. A floor of `1e-9` is a division guard and
  is deliberately **not** flagged; the cutoff is `0.1`.

On three of our own source trees (excluding virtualenvs) it found **36 files**,
**8 HIGH**, **51 MEDIUM**, one parse error. The HIGH files are the compounded
engines; the MEDIUM ones are mostly per-trade floors that need a human look.

## Why a linter and not a proof

A tiny floor is sometimes legitimate: `price = max(price, 1e-9)` guards a division.
The detector cannot tell intent. It points at the line, and the reviewer answers one
question: *if this account were ruined here, should the next bar still trade?*

If the answer is no, return 0 — do not hand it 1%.

## Reproduce

```bash
python3 -m unittest tests.test_bust_revival -v
python3 - <<"PY"
from auditkit.checks import bust_revival
print(bust_revival.detect_file("path/to/engine.py"))
PY
```
