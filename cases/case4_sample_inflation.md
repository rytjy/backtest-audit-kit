# Case 4 (bonus) — Statistical inflation: 5-minute bars fake your sample size

**Symptom.** A signal's edge looked overwhelming: an enormous t-statistic
(t = 15.60) over hundreds of "independent" observations. Live, it was noise.

**Root cause.** The strategy fired a cluster of entries as a market crashed —
a dozen-plus consecutive 5-minute bars, each treated as a separate, independent
sample. The same one market event was counted 11 times, inflating the effective
sample size roughly **11x** and collapsing the standard error. The
t-statistic was an artefact of overlapping, autocorrelated observations.

**What the fix changed.** De-duplicate signals: after an entry, impose a
**24-hour cooldown** so one event yields one observation.

| Variant | Observations (n) | t-statistic |
|---|---|---|
| Raw 5-minute clustering (buggy) | inflated ~11x | **15.60** |
| After 24h cooldown de-dup (fixed) | 526 | **1.75** |

**Bottom line.** Same signal, same market, same period: **t = 15.60 → t = 1.75**.
The "edge" was overlapping samples. Any time your `n` is a count of bars rather
than a count of *independent events*, the significance test is invalid.

*This case is included as a bonus; the shipped checker set focuses on
look-ahead, ledger invariants, mutation coverage and costs. De-duplication is a
one-line assertion in the harness and is left to the operator.*
