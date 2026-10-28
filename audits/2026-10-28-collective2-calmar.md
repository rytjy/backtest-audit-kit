# Four Collective2 strategy pages, zero reproducible Calmar ratios

*Published 2026-10-28. Data read from public Collective2 strategy pages on 2026-10-27. No contact was made with any strategy seller.*

## What this is

Collective2 strategy pages advertise a handful of headline statistics. Three of them are enough to recompute two derived metrics:

- **Calmar ratio** = annualized return ÷ max drawdown
- **Profit factor** = (win % × average win) ÷ ((1 − win %) × average loss)

If the page's own numbers cannot produce the page's own Calmar under that definition, then either the label is loose or one of the inputs comes from a different sample. Either way, the number is not comparable across pages — and buyers rank strategies by it.

Twelve candidate strategy pages were listed. Nine were fetched; five showed all-zero statistics and were excluded as inactive, and four had complete summary blocks. Those four are below.

## Results

| Strategy | Annual return | Max DD | Calmar (page) | Calmar (recomputed) | page ÷ recomputed |
|---|---:|---:|---:|---:|---:|
| 131145247 | 32.4% | 14.1% | 3.52 | 2.30 | **1.53×** |
| 132169961 | 22.3% | 31.8% | 0.95 | 0.70 | **1.35×** |
| 146455121 | 56.9% | 29.7% | 2.76 | 1.92 | **1.44×** |
| 146649042 | 22.8% | 13.4% | 2.06 | 1.70 | **1.21×** |

Profit factor, same pages:

| Strategy | PF (page) | PF (recomputed) | Difference |
|---|---:|---:|---:|
| 131145247 | 1.50 | 1.46 | +2.8% |
| 132169961 | 2.70 | 2.35 | **+14.8%** |
| 146455121 | 3.10 | 3.03 | +2.4% |
| 146649042 | 1.70 | 1.69 | +0.9% |

## What the numbers say

1. **Profit factor is arithmetically coherent on three of four pages.** Win rate × average win over loss rate × average loss lands within 3% of the stated value — rounding-level. This is a good sign: those summary blocks are internally consistent.
2. **Calmar matches none of the four**, and the overshoot is not a constant (1.21× to 1.53×). So it is not one rounding rule and not one missing term. Either the numerator is not "annual return (compounded)" as labelled, the denominator is not the max drawdown shown on the same page, or both.
3. **One page also fails the profit-factor check** (132169961, +14.8%). Either one of its four inputs is stale or comes from a different trade set, or its profit factor is computed over a different sample than the win/loss figures beside it.
4. **Practical consequence:** two strategies showing the same Calmar can have very different return/drawdown combinations, and nothing on the page tells you which definition produced the number. Ranking by it, or paying a monthly fee because of it, is ranking by an unverified quantity.

## What this does **not** say

- It does **not** say any seller is lying. The most likely explanation is a definition difference on the platform side, and the profit-factor check mostly passes.
- I did **not** have trade-level data or the equity curve, so I cannot say *which* field is wrong, and I cannot recompute max drawdown independently.
- I did **not** check whether C2's Calmar uses a rolling-window drawdown, a different annualization, or a different period. Determining that would require the equity series, which these pages do not expose publicly.
- Nothing here is a claim about future performance.

## Reproduce it

`c2_page_check.py` in this directory contains the four rows exactly as read from the pages and recomputes both metrics. The arithmetic is four divisions per page; you can check it by hand from the tables above.

## Why publish this

If you are buying a strategy subscription, ask the seller which definition produced the headline ratio. If the answer is "whatever the platform shows", this is what that is worth.

---

*Scope statement (required by this repo's own rules): verified — the arithmetic relationship between six summary fields on four public pages on 2026-10-27. Not verified — trade-level accuracy, drawdown computation, equity curve, platform metric definitions, future returns. Applies to — these four pages on that date; Collective2 may change its display, and other pages may use different fields.*

