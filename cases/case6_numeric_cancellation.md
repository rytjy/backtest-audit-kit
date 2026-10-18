# Case 6 — R² says 0.6 on a series whose correlation is 1.0

**Symptom.** An expanding R² computed on a perfectly linear series returns
values between 0.14 and 0.69 where the answer is 1.0. No exception, no NaN —
just a plausible-looking number that is wrong.

**Repro.** `y = 100 + 1e-6 * arange(6)` (six points on a line). The raw-moment
form used by the expanding kernel:

```python
num = N*sum(i*y) - sum(i)*sum(y)
den = sqrt((N*sum(i*i) - sum(i)**2) * (N*sum(y*y) - sum(y)**2))
r2 = (num/den)**2
```

gives

```
[nan, 0.137439, 0.206158, 0.687195, 0.572662, 0.601295]
```

while centered moments on the same doubles give

```
[nan, 1.0, 1.0, 1.0, 1.0, 1.0]
```

**Root cause.** `E[y²] − E[y]²` subtracts two nearly equal ~1e4 numbers to
recover a ~1e-12 variance. On this prefix the naive variance is 3.638e-12
against a centered 2.917e-12 — a **24.7% relative error before any mask runs**.
With `y = 1e10 + arange(6)` the same form collapses to
`[nan, nan, 4.58e-5, nan, nan, nan]`; centered moments still give 1.0.

**Why the obvious fix is wrong.** The rolling branch of the same library masks
windows whose absolute standard deviation is near zero. Copying that mask to
the expanding branch is not a fix: an absolute threshold measures numerical
scale, not degeneracy, and it rejects valid small-variance windows together
with the broken ones. Compute centered moments and return NaN only when the
centered variance is exactly zero (or below an epsilon tied to the series
scale).

**What to check in your own backtest.** Any R² / IC / correlation used to rank
models is a ratio of variances. If it is built from raw sum-of-squares, test it
on a linear series at the price levels you actually trade (1e4–1e10) and on a
small-variance window. A correct implementation returns 1.0 or NaN; a naive one
returns something that looks reasonable.

**Bottom line.** Silent numeric error is worse than a crash: the model ranking
still comes out, and it is wrong. A ten-line linear fixture catches this class
in seconds.

**Caveats.** Verified on Python doubles with 6-point sequences, in a pure-Python
reimplementation of the same sums — not against a compiled build, and not
across the library's other metrics. The upstream discussion is public; no claim
is made about its resolution status.

**How to reproduce.** `python3 cases/repro_case6_numeric.py` (standard library
only) prints the naive and centered outputs, both series, and the variance
error.
