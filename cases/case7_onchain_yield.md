# Case 7 — On-chain yield: the APY you see vs the APY you get

**Question.** A vault advertises 8.44% net APY. What did a holder actually
earn over the last 30 and 90 days?

**Method.** For an ERC4626 vault, `convertToAssets(10**shareDecimals)` returns
assets per share. Sample it at the latest block and at blocks ~7/30/90/180
days back; read each block's timestamp; annualize the share-price ratio:

    (pps_now / pps_t) ** (365.25 * 86400 / (t_now - t)) - 1

No indexer, no vendor APY history, no trust in the issuer's dashboard.

Two public vaults, same method.

---

## A. sUSDS (Sky Savings USDS) — an honest headline

| Item | Value |
|---|---|
| Vault | `0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD` (Ethereum) |
| totalAssets | 4,866,313,574 USDS (~$4.87B) |
| price per share | 1.11345598 |
| headline APY | **3.80%** (DeFiLlama, 2026-10-20) |

| Window | pps | Realized APY |
|---|---|---|
| 7 days | 1.11265706 | **3.8027%** |
| 30 days | 1.11013524 | **3.6871%** |
| 90 days | 1.10377501 | **3.5935%** |
| 180 days | 1.09410721 | **3.6074%** |

**Verdict.** The number is honest: 7-day realized equals the headline.
But the headline is a *point-in-time* rate. Over 30/90 days a holder earned
0.11/0.21 pp less. Using 3.80% as a three-month expectation overstates it.

---

## B. Yearn OG USDC (ymvOG-USDC) — a structural gap

| Item | Value |
|---|---|
| Vault | `0xF9bdDd4A9b3A45f980e11fDDE96e16364dDBEc49` (Ethereum) |
| totalAssets | 10,240,839 USDC (~$10.24M) |
| price per share | 1.079601 USDC |
| headline netApy | **8.4368%** |
| netApy excluding rewards | **7.9207%** |
| vault's own avgNetApy | 6.1445% |
| performance fee | 5% |

| Window | pps (USDC/share) | Realized APY |
|---|---|---|
| 7 days | 1.078423 | **5.8413%** |
| 30 days | 1.073987 | **6.5244%** |
| 90 days | 1.064046 | **6.0429%** |
| 180 days | 1.051274 | **5.5222%** |

**Verdict.** The headline overstates the 30-day realized return by **1.92 pp**
and the 90-day by **2.39 pp**. Three separate sources:

1. **Reward tokens (0.52 pp).** `netApy` capitalizes token rewards, but the
   share price only accrues base yield. A holder who does not claim and sell
   the rewards receives `netApyExcludingRewards`, not `netApy`.
2. **Point-in-time vs period.** Even excluding rewards, 7.92% is 1.40 pp above
   the 30-day realized 6.52%. The vault's own `avgNetApy` (6.14%) is the
   comparator that actually matches the realized series.
3. **Gross vs net of fees.** The 5% performance fee is already inside the
   share price; the gross `apy` (8.35%) is not.

---

## Why this matters

Allocators compare headline APY. The realized share-price series is what a
holder actually received. The gap is not one number but three measurable
sources — and none of them requires trusting the issuer's dashboard.

## What this does **not** prove

- One vault per case, one source for each headline, four lookback windows.
- The vault contracts, reward-claim path, and fee-accrual mechanics were not
  audited.
- Scope is the two vaults and the dates shown; the numbers do not generalize.
- The public archive endpoint has no SLA; re-running later will move the
  latest-block window.

## Open lead (not a finding)

DeFiLlama reports `SENPYUSDMAIN` at **$388M TVL / 5.34%** (2.33% base + 3.00%
reward). Morpho's own API lists the Sentora PYUSD vaults at near-zero TVL and
3.4–3.8% net. **Two public sources disagree by ~$388M on the same object.**
Resolving it needs the vault address and on-chain `totalAssets`; until then it
is a lead, not a conclusion.

## Reproduce

```bash
python3 cases/repro_case7_yield.py --vault 0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD --reported 3.80
python3 cases/repro_case7_yield.py --vault 0xF9bdDd4A9b3A45f980e11fDDE96e16364dDBEc49 --reported 8.4368
```
