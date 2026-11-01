# Case 11 — Multiplicity: 1,701 trials and a bar that measures the search

> **Provenance.** The figures in the table below are **not recomputed in this
> repository**. They were re-derived from the target's own published output —
> `BrockStar3540/mr-scrooge-v6`, pre-registration commit `48f82bf9`
> (2026-10-21 21:01Z), `research/deflation/results.json` generated 21:04Z.
> That file is not vendored here: verifying the arithmetic means cloning their
> repository at that commit. What this write-up stands behind is the thread and
> the commit sequence, not a local re-run.

**Symptom.** A repo promoted setups to live capital when they cleared an
"evidence bar": n >= 10 episodes over >= 5 independent days, a day-block
bootstrap LCB > 0 (10,000 reps), and Benjamini-Hochberg FDR at q = 0.10. About
1,700 setups had been scored. The question was not whether the bar was
implemented correctly — it was whether clearing it meant anything at that
trial count.

**The challenge.** The bar's *m* is the set of setups that reached the
counting gates, not the set of setups that were tried. A survivor's score
therefore carries selection from everything that never made the docket. A fixed
threshold out of 1,701 candidates is not the same object as one out of 10.

**What the maintainer did.** Two weeks later he replied, conceded the three
parts that landed (BH family != full search; the registry lived in a gitignored
`data/`; DSR and PBO had never been run), then **pre-registered the test before
computing it** — commit `48f82bf9` at 21:01Z, `results.json` generated at
21:04Z — and published the answer against himself.

**Result** (re-derived here from `research/deflation/results.json`, not quoted
from the comment):

| Quantity | Value |
|---|---|
| Setups ever seated | 163 of 1,701 registered |
| Median daily Sharpe of seated setups | 0.128 |
| Median deflated Sharpe (DSR, N = 1,701) | **0.00** |
| Seated setups with DSR >= 0.95 | **0** (2 above 0.5) |
| Median DSR at effective N ~ 42.4 | 0.010 |
| CSCV PBO, bar replica (S = 16, 12,870 splits) | 0.032 |
| CSCV PBO, best-in-sample pick | 0.190 |
| Equal-weight book: SR/day · PSR · DSR | 0.364 · 0.999 · **0.0034** |

**The part worth keeping.** At N = 1,701 over 85 market days, a zero-skill
best-of-N is expected to show ~0.67/day, so a median DSR of zero is close to
forced: even the book, at 0.364/day and PSR 0.999, deflates to 0.0034. The
honest reading is not "no edge exists" but "**this sample cannot separate edge
from 1,701 draws**". The sample length, not the bar, is the binding constraint.

**Lesson for the kit.** Two artifacts decide this question, and neither is a
statistical test: a **public registry of every trial** (including those never
promoted) and a **pre-registered verdict rule**. A bar that does not scale with
N certifies the search, not the edge. Check for both before reading any
promoted-set Sharpe.

*Public thread: BrockStar3540/mr-scrooge-v6#9 — opened 2026-10-08, answered
2026-10-21 (comments 6325714679, 6327521602; our reply 6332941971). Registry:
`research/registry/` (1,701 setups · 2,915 config versions · 9,054 decisions).*

