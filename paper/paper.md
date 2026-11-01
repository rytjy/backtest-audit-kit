# Thirty-two replications: what actually breaks in published backtests

**Working paper · draft 1 · 2026-11-01**
*Not submitted. No venue chosen yet. Sample, method and every number below are reproduced by
`paper/data/threads.csv` and the per-case write-ups in `cases/`.*

---

## Summary

Between 2026-09-30 and 2026-11-01 I opened 32 public issues against published backtests,
backtesting libraries and one family of deployed contracts, each reporting a specific, checkable
defect. This note records what the set contains, what came back, and where the failures cluster.

Three observations, in order of how much they surprised me:

1. **The failures are mostly about measurement, not about alpha.** Eight of 32 are library
   correctness bugs; a further eleven are definitional - the number reported is computed on a
   different basis than the number a reader would assume. Only two are classic look-ahead.
2. **Roughly a third answered.** Ten of 32 threads received at least one reply from someone other
   than me (two threads unverified at time of writing). Two of those produced a documented change
   in the target's own repository.
3. **Nobody paid, and nobody was asked to.** The project this sample comes from has produced zero
   revenue. That is a fact about distribution, not about the findings, and it is reported here
   because leaving it out would make the rest look like a sales track record.

## What this is, and what it is not

It is a convenience sample of one reviewer's public work, with the raw thread list attached. It is
not a random sample of published backtests, it has no control group, and the reviewer is also the
author of the tooling used to find the defects - both facts bound what can be concluded.

It is also not an accusation. Every defect below is consistent with ordinary engineering debt. The
scripts that survive are the ones people ship; the ones with a wrong denominator are simply the ones
nobody recomputed.

## Sample and protocol

- **Window:** 2026-09-30 to 2026-11-01.
- **Unit:** one public issue per target, containing a specific numeric claim, the artifact that
  contradicts it, and a reproducible command or script.
- **Target selection:** public repositories that publish backtest results, performance tables, or
  backtesting machinery. Selection was opportunistic - a target entered the sample when a number on
  a page could be recomputed from something else on the same page.
- **Outcome recorded:** (a) any reply from a party other than the reviewer, (b) thread state,
  (c) whether a change to the target's code or documentation followed. No follow-up pressure was
  applied beyond the thread itself.

The raw list is `paper/data/threads.csv`: 32 rows, columns `repo, number, opened, state, comments,
outside, class, title`. The `outside` column names the responding accounts; `unverified` marks the
two threads whose comment authorship had not been retrieved when this draft was written.

## Taxonomy

Each thread was assigned one class by the reviewer. This is a single coder with no second rater, so
the counts are indicative rather than measured.

| Class | n | What it means | Example |
|---|---|---|---|
| Library correctness | 8 | the function returns something other than what its name and docs promise | `ewm_std` ignores `ddof` |
| Smart-contract accounting | 6 | deployed code whose stated invariant does not hold | `pegBand` silently disabled |
| Metric definition | 4 | the reported number is computed on a basis the page does not state | trailing-stop bucket graded at 100% P&L tolerance |
| Provenance | 3 | a headline number with no code path that produces it | DSR 97.7 with no audit script |
| Data integrity | 2 | rows or days that cannot be what they claim | equity moves on zero-fill days |
| Look-ahead | 2 | information from the future reaching the decision | point-in-time rename under a current mapping |
| Multiplicity | 2 | a fixed evidence bar applied to a search of unknown size | 1,701 trials, one threshold |
| Install / runtime | 2 | the artifact does not start | `pkg_resources` removed upstream |
| Cost accounting | 2 | fees, financing or dividends treated inconsistently | 5 days of weekend financing for a 3-day swap |
| Documentation | 1 | the example asserts the wrong behaviour | `MultiBacktest` docstring |

The distribution is the finding. If the popular worry - "this strategy has no edge and the author
knows it" - were the dominant failure mode, look-ahead and multiplicity would dominate the table.
They are four cases out of 32. The bulk is arithmetic that nobody re-derived: a denominator, a
tolerance, a `ddof`, a scale factor, a weekend.

That matters for anyone who buys verification. **You do not need a market view to catch most of
these. You need the second number.**

## Response

| | n |
|---|---|
| Threads opened | 32 |
| Received a reply from someone else | 10 |
| Unverified | 2 |
| Closed | 3 |
| Accepted, with a change committed | 2 |

The two accepted cases are the ones with a written outcome:

- **pineforge-engine #664.** The parity scoreboard reports 7,989 graded probes under one headline;
  341 of them are graded on a 100x looser P&L tolerance. Reply the same day: the split is real,
  the bucket will be listed separately, the 341-row per-probe table published first, re-run by
  2026-11-04.
- **mr-scrooge-v6 #9.** A promote/demote evidence bar that does not scale with the number of trials.
  Reply two weeks later, after the maintainer pre-registered and then published a test against
  himself; the ratchet was re-tightened and a config-loader bug fixed the same night.

Both replies are in the threads. Neither was solicited with an offer.

## What the numbers do not show

- **No base rate.** 10 of 32 is a property of this sample, not of published backtests in general.
  Targets were chosen because a number looked recomputable; the population that never gets
  recomputed is invisible here.
- **No causal claim about replies.** A thread that gets answered may be one where the maintainer is
  active, where the defect is cheap to confirm, or where the tone landed. This design cannot
  separate those.
- **No revenue.** Zero paid engagements. The response rate measures whether the defect is real and
  legible; it says nothing about willingness to pay.
- **The smart-contract cases are a different population** (deployed code, contest submissions) and
  are included only to keep the list complete, not to support the taxonomy counts above.

## Availability

- Thread list: `paper/data/threads.csv`
- Per-case write-ups: `cases/` (11 files, each with a reproduction script where one exists)
- Toolkit: `auditkit/` - look-ahead linter, cost model, deflation, metric reconciliation
- A worked example of the deliverable: `audits/2026-11-01-sample-verification-report.pdf`

## Next

Two things would make this more than a working note: a second coder on the taxonomy (inter-rater
agreement on 32 rows is cheap), and a denominator - how many public backtests exist in the
repositories sampled, so "we found 32" becomes "32 of N". Neither is in this draft.
