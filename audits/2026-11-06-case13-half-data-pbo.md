# Case 13 — half the tickers, twice the PBO

> Written 2026-11-06. This one is a **retraction**, not a finding: on 2026-11-05
> I published a PBO of 73.33% against a README that claimed 20%. The full-universe
> re-run gives 46.67%, which matches the maintainer's own correction. The 73.33%
> was an artifact of running with 63 of 75 tickers. Everything below is
> reproducible from the public repository plus the commit named here.

Thread: <https://github.com/ramuza0113-sketch/lumina-ai-hedge-fund/issues/4>
Correction comment: `6682475801` (2026-11-06T10:14:48Z).

## What was published

On 2026-11-05 I ran `bddb048` with its own scripts:

| metric | README table | my run (63/75 tickers) |
|---|---|---|
| CPCV median OOS Sharpe | 1.29 | 1.09 |
| negative folds | 0/15 | 0/15 |
| PBO | 20.0% | **73.33%** |
| DSR | 97.76% | 99.14% |
| WFE | 89.6% | 73.3% |

PBO 73.33% is above the script's own 50% hard-reject line, so I wrote that the
row "should be corrected". That claim rested on a data set that was not the one
the repository describes.

## What was actually wrong

`load_5year_data()` downloads 75 tickers with `yf.download(threads=True)`.
Yahoo throttles 75 concurrent requests; the loader had

```python
except Exception:
    continue
```

so every failed ticker disappeared silently. The first run loaded **63/75
tickers (52/64 primary universe)**. The 12 missing names were mostly Tokyo
listings (`.T`), i.e. a whole market segment, not a random sample.

The maintainer fixed exactly this in `332951e` (2026-11-05T13:17:57Z, 2 files,
46 lines): sequential fallback with retries, plus a loud `Loaded N/M` line.

## Why it changes PBO, specifically

PBO/CSCV is a **rank** statistic. For each of 15 splits it ranks the 9 (or 13)
configurations by in-sample performance, then asks how often the in-sample
winner lands below the median out-of-sample. Dropping 12 tickers does not just
shrink the sample — it changes the return of *every* configuration on *every*
day, so every cross-sectional percentile moves. The "best" configuration can
change identity. A PBO computed on a different universe is not a noisy version
of the same test; it is a different test.

The same applies to CPCV (fold composition changes) and to WFE (window returns
change), which is why all three moved together.

## Full universe vs half

Same commit, same scripts, same snapshot date:

| metric | 63/75 (2026-11-05) | 75/75 (2026-11-06) | maintainer |
|---|---|---|---|
| tickers / universe | 63 / 52 | **75 / 64** | 75 / 64 |
| CPCV median OOS SR | 1.09 | **1.3027** (mean 1.3584) | 1.30 (mean 1.36) |
| negative folds | 0/15 | **0/15** | 0/15 |
| PBO strict IS-argmax | 73.33% (11/15) | **46.67% (7/15)** | 46.67% (7/15) |
| PBO baseline sub-median | — | **26.67% (4/15)** | 26.67% (4/15) |
| DSR | 99.14% | **98.11%** (SR0 0.1844) | 99.14% |
| WFE | 73.3% | **89.4% / 91.3%** (two runs) | 89.5% |

Full universe reproduces the maintainer's CPCV and PBO **to the digit**. DSR is
1.03pp lower than their number but still above the 0.95 line. WFE sits within
2pp of their 89.5%; the residual is window 7's IS CAGR (32.84% vs 28.93%),
which follows from yfinance's adjusted-price snapshot, not from the code.

## The "fix" is probabilistic

Their sequential fallback retries **3 times**. Run as-is, one of my re-runs
still loaded only **71/75** — four tickers (`8306.T`, `9433.T`, `7013.T`,
`7201.T`) failed all three attempts. Raising `range(3)` to `range(12)` with
`sleep(1)` between attempts loaded 75/75 on both subsequent runs.

So the correct reading of `332951e` is: **the silent-drop bug is fixed, the
75/75 guarantee is not**. Any audit that prints a rank statistic must assert
the loaded count first.

## What I changed in my own process

Added to the pre-run checklist (and to this kit's usage notes):

1. Print `loaded / universe / days` and **abort the PBO/CPCV block** if the
   counts differ from the repository's stated universe.
2. Treat `except Exception: continue` in a data loader as a **finding by
   itself** — it converts a network failure into a silent universe change.
3. When re-running a fixed commit, do not assume determinism: run the loader
   twice and compare counts before trusting either result.

## Scope

- Verified: commit `332951e`, 1,510 trading days (2021-01-04 to 2026-10-23),
  75/75 tickers, CPCV / PBO / DSR / WFE as tabulated.
- Not verified: the repository's remaining claims (Monte Carlo, 20-point audit
  matrix) and its production track record. Nothing here endorses the strategy —
  only the four numbers above.
- The retracted number stays visible in the 2026-11-05 case write-up
  (`audits/2026-11-05-lumina-pbo.md`) with a pointer to this file; deleting it
  would hide the error that produced it.
