#!/usr/bin/env python3
"""Work sample 02: one rule, fully reproducible, with its own deflation checks.

Data: btc_daily.csv (BTCUSDT 1d, downloaded from data.binance.vision, 2019-01-01..2026-09-29).
Rule: RSI(14) mean reversion, long only, full equity.

Design choices that matter:
  - signal on close t, execute at open t+1 (no look-ahead)
  - 10 bps fee per side, no leverage, no shorting
  - all 9 parameter variants reported, not just the best
  - 70/30 in-sample / out-of-sample split fixed before looking
"""
import csv, json, math
from datetime import datetime, timezone

FEE = 0.0010

def load():
    rows = []
    with open("btc_daily.csv") as f:
        for r in csv.DictReader(f):
            rows.append({"id": int(r["ts"]), "open": float(r["open"]), "close": float(r["close"])})
    rows.sort(key=lambda k: k["id"])
    return rows

def rsi(closes, n=14):
    out = [None] * len(closes)
    gains = losses = 0.0
    ag = al = None
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i-1]
        g, l = max(ch, 0.0), max(-ch, 0.0)
        if i <= n:
            gains += g; losses += l
            if i == n:
                ag, al = gains / n, losses / n
                out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
        else:
            ag = (ag * (n - 1) + g) / n
            al = (al * (n - 1) + l) / n
            out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out

def backtest(ks, entry=30.0, exit_=55.0, max_hold=10):
    closes = [k["close"] for k in ks]
    r = rsi(closes)
    eq, curve, trades = 1.0, [], []
    pos = None
    for i in range(1, len(ks)):
        o = ks[i]["open"]
        if pos is None:
            if r[i-1] is not None and r[i-1] < entry:
                pos = {"i": i, "px": o * (1 + FEE)}
        else:
            held = i - pos["i"]
            hit = (r[i-1] is not None and r[i-1] > exit_) or held >= max_hold
            if hit:
                px = o * (1 - FEE)
                ret = px / pos["px"] - 1
                eq *= (1 + ret)
                trades.append({"in": ks[pos["i"]]["id"], "out": ks[i]["id"], "ret": ret, "held": held})
                pos = None
        curve.append({"t": ks[i]["id"], "eq": eq})
    return eq, trades, curve

def metrics(eq, trades, curve, years):
    rets = [b["eq"] / a["eq"] - 1 if a["eq"] else 0.0 for a, b in zip(curve, curve[1:])]
    mean = sum(rets) / len(rets) if rets else 0.0
    var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1) if len(rets) > 1 else 0.0
    sd = math.sqrt(var)
    sharpe = (mean / sd * math.sqrt(365)) if sd else 0.0
    peak, mdd = curve[0]["eq"], 0.0
    for p in curve:
        peak = max(peak, p["eq"])
        mdd = min(mdd, p["eq"] / peak - 1)
    wins = [t for t in trades if t["ret"] > 0]
    return {"total_return": eq - 1,
            "cagr": eq ** (1 / years) - 1 if years > 0 else None,
            "max_drawdown": mdd, "sharpe": sharpe,
            "trades": len(trades),
            "win_rate": len(wins) / len(trades) if trades else None,
            "avg_hold_days": (sum(t["held"] for t in trades) / len(trades)) if trades else None}

def main():
    ks = load()
    span = (ks[-1]["id"] - ks[0]["id"]) / (365.25 * 86400 * 1000)
    cut = int(len(ks) * 0.7)
    grid = [(e, x) for e in (25.0, 30.0, 35.0) for x in (50.0, 55.0, 60.0)]
    rows = []
    for e, x in grid:
        eq, tr, cv = backtest(ks, e, x)
        m = metrics(eq, tr, cv, span)
        iso_eq, iso_tr, iso_cv = backtest(ks[:cut], e, x)
        oos_eq, oos_tr, oos_cv = backtest(ks[cut:], e, x)
        rows.append({"entry": e, "exit": x, "full": m,
                     "is_cagr": metrics(iso_eq, iso_tr, iso_cv, span * 0.7)["cagr"],
                     "oos_cagr": metrics(oos_eq, oos_tr, oos_cv, span * 0.3)["cagr"],
                     "oos_trades": len(oos_tr)})
    best = max(rows, key=lambda r: r["is_cagr"] if r["is_cagr"] is not None else -9)
    med = sorted([r["is_cagr"] for r in rows if r["is_cagr"] is not None])
    out = {"symbol": "BTCUSDT", "bars": len(ks),
           "start": datetime.fromtimestamp(ks[0]["id"]/1000, timezone.utc).strftime("%Y-%m-%d"),
           "end": datetime.fromtimestamp(ks[-1]["id"]/1000, timezone.utc).strftime("%Y-%m-%d"),
           "years": round(span, 2), "fee_per_side": FEE, "grid": rows,
           "best_by_is": best, "median_is_cagr": med[len(med)//2] if med else None,
           "oos_decay": (best["oos_cagr"] - best["is_cagr"]) if best["is_cagr"] is not None else None}
    json.dump(out, open("results.json", "w"), indent=2)
    print(json.dumps({k: out[k] for k in ("bars", "start", "end", "years", "median_is_cagr", "oos_decay")}, indent=2))
    for r in rows:
        print("entry %.0f exit %.0f | IS %6s | OOS %6s | trades %3d | MDD %6.1f%%" % (
            r["entry"], r["exit"],
            ("%.1f%%" % (r["is_cagr"]*100)) if r["is_cagr"] is not None else "n/a",
            ("%.1f%%" % (r["oos_cagr"]*100)) if r["oos_cagr"] is not None else "n/a",
            r["full"]["trades"], r["full"]["max_drawdown"]*100))

if __name__ == "__main__":
    main()