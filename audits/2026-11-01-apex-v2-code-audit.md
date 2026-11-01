# APEX V2 [JOAT] - six defects, found by reading the source

A source-level audit of a published open-source Pine strategy. No execution, no account access,
no trades placed. Every finding below is a line number in the script the author publishes.

- **Target:** https://www.tradingview.com/script/b4EWZCPJ-APEX-V2-JOAT/ (author: JOAT)
- **Access:** open. `scriptAccess: open_no_auth` in the pine-facade record; the source is public.
- **Source retrieved:** 2026-11-01 via
  `https://pine-facade.tradingview.com/pine-facade/get/PUB%3B9afe992842d04ba1bd20586ce2f015e3/1/`
  `script_id_part = PUB;9afe992842d04ba1bd20586ce2f015e3`
- **Artifact:** 1,054 lines, 52,416 characters (63,707 bytes, UTF-8),
  sha256 `d0e4885c096fc376859c26bda15d337f69e19ba5e074e2cb818efeb1ec0ca997`
- **Method:** map each numeric claim in the description to the code that implements it; report only
  where the two disagree. Nothing here depends on running the strategy.

## Findings

| # | What the script says | What the code does | Lines |
|---|---|---|---|
| 1 | VWAP deviation `8.0σ` (2m/5m), `4.0σ` (15m) | the default denominator is `ta.stdev(price, 20) * 1.5`, so `8.0` is a 12-sigma gap | 214-233, 58-60 |
| 2 | "Minimum Confluence Count", 9 indicators | `bull_signals` sums 9 terms, `min_confluence` is capped at `maxval=7` | 44, 675-696, 919 |
| 3 | nine independent modules agree | two of the nine votes are the same VWAP deviation | 268-278, 553-563 |
| 4 | "Enable Trailing Stop" (default on) | `limit` and `trail_price` sit at the same price; the limit fills first | 737-752 |
| 5 | "Risk Per Trade %" | `position_size` is computed and never used; sizing is `default_qty_value=100` | 716-721, 734-735 |
| 6 | - | `strategy()` sets no commission and no slippage | 4-15 |

### 1. The sigma is not a sigma

`f_calculate_vwap_deviation(price, vwap_val, method)` has three branches. The default is
`"Price Volatility"`, which sets `denominator := price_stdev * 1.5`. The `"Z-Score (Canonical)"`
branch uses plain `price_stdev` - that one is a real sigma count, and it is not the default.

So the dashboard tile that prints `8.0σ` is reporting a deviation of twelve standard deviations.
An actual 12-sigma VWAP gap is roughly a once-in-the-sample event on any liquid instrument; a
genuine 8-sigma gap is already extreme. The number is internally consistent, but the unit on the
label is wrong by a factor of 1.5, and the strategy's own description repeats the wrong unit.

### 2. Nine votes, but you cannot ask for eight

`bull_signals`/`bear_signals` each add nine terms, and the dashboard prints `"/9"`. The input that
gates them, `min_confluence = input.int(3, ..., minval=1, maxval=7)`, caps at 7 and its tooltip reads
"Number of indicators". A user who wants 8 of 9 agreement cannot express it. Either the cap or the
denominator is wrong; both cannot be right.

### 3. Two of the nine votes measure the same thing

FAM (`lad_absorption_buy`) and VWAP Tension (`vwap_tension_buy`) both evaluate
`|price - ta.vwap(hlc3)|` against a threshold, through the same three-branch deviation function.
What differs is the extra filter: FAM additionally requires a volume surge (2.25x the 45-bar average)
and RVOL above 0.6; VWAP Tension adds a gap threshold. The underlying measurement is identical.

That matters because `entry_long` fires at `bull_signals >= min_confluence`, with
`min_confluence` defaulting to 3. Two correlated VWAP votes plus any one other module clears the bar.
The confluence counter reads as nine independent witnesses; in practice the effective number is
smaller, and it is smaller precisely on the setups where both VWAP modules fire together.

### 4. The trailing stop can never fire

```pine
strategy.exit("LONG EXIT", "LONG",
             stop=long_stop,
             limit=use_take_profit ? long_target : na,
             trail_price=use_trailing ? long_target : na,
             trail_offset=use_trailing ? close * (trailing_pct / 100) : na)
```

`trail_price` is the price at which the trailing stop activates; `limit` is a resting order at the
same `long_target`. The limit order fills when price reaches the target, which is the same tick that
would arm the trail. The trail never gets to run. `use_trailing` ships `true` and
`trailing_pct = 1.5`, so the input is live, documented, and inert.

This one is worth flagging by itself: a default-on setting that cannot execute is the kind of thing
that gets copied into other scripts.

### 5. Position sizing is dead code

Lines 716-721 compute `account_size`, `risk_amount = account_size * (risk_per_trade / 100)`,
`stop_distance = atr * (stop_loss_pct / 100)` and `position_size = risk_amount / stop_distance`.
`position_size` is never referenced again - the only later uses are `strategy.position_size`, a
different variable. Entries go through `default_qty_type=strategy.percent_of_equity,
default_qty_value=100`.

So "Risk Per Trade %" (default 2.0) does nothing, and every trade is sized at 100% of equity.
The block reads as risk management and is not connected to anything.

### 6. No commission, no slippage

`strategy("APEX V2", ...)` declares `initial_capital`, `default_qty_type`, `default_qty_value`,
`pyramiding`, `calc_on_every_tick` and the drawing limits. It declares no `commission_type`,
`commission_value` and no `slippage`.

With 100% of equity per position, a 2% stop and a 4% target, the omission is not cosmetic: the
Strategy Tester output is gross of every cost. On a 5-minute crypto chart the round trip is a
material share of the 2% stop distance.

## What this audit does not say

- **It does not say the strategy loses money.** I did not run it, and I make no claim about its
  equity curve. Six implementation defects and a negative expectancy are different findings.
- **It does not say the author is dishonest.** Every defect above is consistent with a large
  hand-written script: a helper written once and called twice, an input added later than the sum it
  gates, an exit call composed from copied lines. The findings are about what the code does, not why.
- **The claim set is bounded.** I checked the numeric claims in the description against the code.
  I did not review the nine modules' math for correctness on their own terms, and I did not verify
  the published performance figures.

## Why there is no reply attached

TradingView script pages have no comment thread. This is not a guess:

- the script page HTML is 706,017 bytes and contains the string `comment` exactly twice - once as
  `comments_count: 0` in the entity record, once as `enable_idea_spamdetectorml_comments` in a
  feature flag. `reply` and `discussion` appear zero times.
- `/api/v1/comments/`, `/api/v1/comments/create/`, `/api/v1/scripts/comments/`,
  `/api/v1/scripts/4955834/comments/` and `/api/v1/script_comments/` all return 404 on both GET and
  POST - the routes do not exist, rather than rejecting the method.
- the one live route, `/api/v1/ideas/comments/`, answers `{"detail":"No Chart matches the given
  query."}` for every entity form tried (`script:<id>`, `chart:<id>`, `idea:<id>`, bare id).

So the critique can only be delivered as an Idea post or a private message, both of which need a
browser session this environment does not have. It is published here instead, where it can be read
and checked line by line.

## Reproduce

```bash
# 1. the source, as served to anyone
curl -s 'https://pine-facade.tradingview.com/pine-facade/get/PUB%3B9afe992842d04ba1bd20586ce2f015e3/1/' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["source"])' > apex.pine
sha256sum apex.pine   # d0e4885c096fc376859c26bda15d337f69e19ba5e074e2cb818efeb1ec0ca997

# 2. each finding, at the line cited
sed -n '214,233p' apex.pine   # deviation method and the *1.5
sed -n '44p'      apex.pine   # maxval=7
sed -n '737,742p' apex.pine   # limit and trail_price at the same price
sed -n '716,721p' apex.pine   # position_size, computed once
sed -n '4,15p'    apex.pine   # strategy() without commission or slippage
```
