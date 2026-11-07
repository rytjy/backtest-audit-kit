# Case 15 — a +90.2% annualised claim, recomputed

**Source:** Collective2 marketing email, "Trading Strategy of the Week: Adaptive Investments", 2026-11-06 15:07Z.
**Claim under test:** *Hypothetical Annual Return (Compounded) +90.2%*.
**Verdict:** the arithmetic is consistent with the published monthly table. The number is **hypothetical**, not an audited real-money return, and it is carried by a small number of months.

## 1. What the email says

- Manager runs the strategy with real money in an Interactive Brokers account; $3,521,990 of real capital follows it; 217 others follow.
- The first line of the email is *"All results are hypothetical."*
- Monthly table (%, sign as printed):

| Year | months |
|---|---|
| 2024 | -3.8, +8.3, -0.5, -7.9, +5.3, +3.9, +4.5 |
| 2025 | +8.5, +0.1, +0.6, +50.7, +7.6, +4.5, +3.3, +10.9, -, +6.2, +12.4, +10.7 |
| 2026 | +14.1, +23.4, -20.9, +20.3, -6.1, -8.9, -3.9, +2.8, +9.3, +18.5, +2.2, +50.1 |

## 2. What I recomputed

Compounding the monthly cells:

- 2024 (7 months): **+9.16%**
- 2025 (11 months, September missing): **+180.27%** — the email prints YTD +180.4%
- 2026 (11 months): **+49.9%** — the email prints YTD +50.1%
- Full span: **~+350%**, which annualises to **~90.3%** on the email's own basis ⇒ the +90.2% is arithmetically consistent.

## 3. What the number hides

- **Concentration.** The three largest months are +50.7%, +23.4%, +20.3% (plus one +180.4% YTD figure). Remove the three largest monthly cells and the annualised figure falls to **~34.8%**.
- **Drawdown.** On monthly closes the worst peak-to-trough is **-21.8%**; 2026 has a -20.9% month followed by -6.1%, -8.9%, -3.9%.
- **Basis.** The displayed track record is a model account. C2's own disclaimer says *"there is no single real-life trading account that looks exactly like the track record shown here."* The "Trades-Own-Strategy" badge certifies the manager trades it with his own money; it does not turn the displayed curve into an audited statement.
- **Costs.** C2 states profits are reinvested and fees are estimated, not taken from a broker statement.

## 4. Scope and limits

- Recomputed **only** from the monthly percentages printed in the email; no trade data, no daily equity, no broker statement.
- I did not verify the manager's real account, the $3.52M figure, or the "Top 1%" rank.
- This note is about the *claim*, not about the strategy's future returns.

## 5. How to use it

If a seller quotes a compounded annual figure, ask for the monthly cells and recompute three things: the compounding, the figure without the top three months, and the worst monthly peak-to-trough. Those three take minutes and separate "arithmetically consistent" from "durable".
