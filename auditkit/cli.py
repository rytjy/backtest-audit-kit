"""auditkit.cli -- one command, three checks on a backtest CSV.

    python3 -m auditkit.cli trades.csv
    python3 -m auditkit.cli trades.csv --trials 200 --split 0.6
    python3 -m auditkit.cli trades.csv --trials 20 --timeframes 5
    python3 -m auditkit.cli trades.csv --ohlc bars.csv --json

Three questions, in the order that kills strategies:

    1. look-ahead       are the timestamps / prices physically possible?
    2. multiple testing is this Sharpe distinguishable from the best of N tries?
    3. oos decay        does the edge survive the second half of the sample?

Pure standard library (Python 3.9+). Exit codes: 0 = every check PASS,
1 = at least one FAIL, 2 = at least one UNVERIFIED and no FAIL.
"""

import argparse
import csv
import datetime as dt
import json
import math
import os
import sys

DATE_KEYS = ("date", "time", "timestamp", "datetime", "open_time", "entry_time", "exit_time", "ts")
EQUITY_KEYS = ("equity", "nav", "balance", "capital", "portfolio_value", "cum_equity", "account_value")
PNL_KEYS = ("pnl", "profit", "net_pnl", "realized_pnl", "pnl_abs")
RET_KEYS = ("return", "returns", "ret", "pnl_pct", "return_pct", "pct")
ENTRY_KEYS = ("entry_price", "entry", "open_price")
EXIT_KEYS = ("exit_price", "exit", "close_price")
HIGH_KEYS = ("high", "bar_high")
LOW_KEYS = ("low", "bar_low")

VERDICT_ORDER = {"FAIL": 0, "UNVERIFIED": 1, "WARN": 2, "PASS": 3, "NODATA": 4}


def _pick(fields, keys):
    lowered = {f.lower().strip(): f for f in fields}
    for k in keys:
        if k in lowered:
            return lowered[k]
    for k in keys:
        for low, orig in lowered.items():
            if k in low:
                return orig
    return None


def parse_date(value):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        f = float(s)
        if f > 1e11:
            f = f / 1000.0
        if f > 1e8:
            return dt.datetime.utcfromtimestamp(f)
    except ValueError:
        pass
    s2 = s.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(s2)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        return (reader.fieldnames or []), rows


def to_float(value):
    if value is None:
        return None
    s = str(value).strip().replace(",", "").replace("$", "").replace("%", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def normal_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def binom_sf(k, n, p=0.5):
    """P(X >= k) for X ~ Binomial(n, p)."""
    if n <= 0:
        return 1.0
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return min(1.0, total)


def sharpe_per_period(returns):
    """Per-period Sharpe (mean / sample sd). Annualise at the call site."""
    if len(returns) < 3:
        return None, None
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    sd = math.sqrt(var)
    if sd <= 0:
        return None, mean
    return mean / sd, mean


def sharpe(returns, ppy):
    per, mean = sharpe_per_period(returns)
    if per is None:
        return None, mean
    return per * math.sqrt(ppy), mean


def infer_ppy(stamps):
    deltas = []
    for a, b in zip(stamps, stamps[1:]):
        if a and b and b > a:
            deltas.append((b - a).total_seconds())
    if not deltas:
        return 252.0, "假设 252 个交易日/年（无时间戳）"
    deltas.sort()
    median = deltas[len(deltas) // 2]
    if median <= 0:
        return 252.0, "时间戳不可用，假设 252"
    if 0.5 * 86400 <= median <= 4 * 86400:
        return 252.0, "按交易日 252/年（中位间隔 %.1f 天）" % (median / 86400.0)
    ppy = 365.25 * 86400.0 / median
    return max(1.0, min(ppy, 525600.0)), "按日历频率 %.0f/年（中位间隔 %.1f 天）" % (ppy, median / 86400.0)


def load_series(path):
    fields, rows = read_csv(path)
    if not rows:
        return None
    cols = {
        "date": _pick(fields, DATE_KEYS),
        "equity": _pick(fields, EQUITY_KEYS),
        "pnl": _pick(fields, PNL_KEYS),
        "ret": _pick(fields, RET_KEYS),
        "entry": _pick(fields, ENTRY_KEYS),
        "exit": _pick(fields, EXIT_KEYS),
    }
    out = []
    for row in rows:
        ts = parse_date(row.get(cols["date"])) if cols["date"] else None
        out.append({
            "ts": ts,
            "equity": to_float(row.get(cols["equity"])) if cols["equity"] else None,
            "pnl": to_float(row.get(cols["pnl"])) if cols["pnl"] else None,
            "ret": to_float(row.get(cols["ret"])) if cols["ret"] else None,
            "entry": to_float(row.get(cols["entry"])) if cols["entry"] else None,
            "exit": to_float(row.get(cols["exit"])) if cols["exit"] else None,
            "raw": row,
        })
    return {"fields": fields, "cols": cols, "rows": out}


def build_returns(series, initial=10000.0):
    rows = series["rows"]
    rets = []
    source = ""
    if any(r["equity"] is not None for r in rows):
        eq = [r["equity"] for r in rows if r["equity"] is not None]
        for a, b in zip(eq, eq[1:]):
            if a != 0:
                rets.append(b / a - 1.0)
        source = "equity -> 逐期收益"
    elif any(r["ret"] is not None for r in rows):
        rets = [r["ret"] for r in rows if r["ret"] is not None]
        if rets and max(abs(x) for x in rets) > 1.5:
            rets = [x / 100.0 for x in rets]
        source = "return 列"
    elif any(r["pnl"] is not None for r in rows):
        rets = [r["pnl"] / initial for r in rows if r["pnl"] is not None]
        source = "pnl / %.0f 初始资金" % initial
    return rets, source


def check_lookahead(series, ohlc_path=None):
    rows = series["rows"]
    findings = []
    stamps = [r["ts"] for r in rows]
    known = [s for s in stamps if s is not None]
    if known:
        bad = sum(1 for a, b in zip(known, known[1:]) if b < a)
        if bad:
            findings.append(("FAIL", "%d 处时间戳倒退：时间不可信，整份回测不能当时间序列处理" % bad))
        dup = len(known) - len(set(known))
        if dup:
            findings.append(("WARN", "%d 行时间戳重复（同一 bar 多笔，需确认不是重复记账）" % dup))
    if series["cols"].get("entry") and series["cols"].get("exit"):
        same = sum(1 for r in rows if r["entry"] is not None and r["entry"] == r["exit"])
        if same:
            findings.append(("WARN", "%d 笔 entry==exit 价格：零持有（同 bar 进出）在多数市场不可成交" % same))

    if ohlc_path:
        bar_fields, bar_rows = read_csv(ohlc_path)
        hi = _pick(bar_fields, HIGH_KEYS)
        lo = _pick(bar_fields, LOW_KEYS)
        dd = _pick(bar_fields, DATE_KEYS)
        bars = {}
        for row in bar_rows:
            day = parse_date(row.get(dd)) if dd else None
            h, l = to_float(row.get(hi)) if hi else None, to_float(row.get(lo)) if lo else None
            if day and h is not None and l is not None:
                bars[day.date()] = (h, l)
        outside = 0
        at_extreme = 0
        checked = 0
        for r in rows:
            if not r["ts"] or r["entry"] is None:
                continue
            bar = bars.get(r["ts"].date())
            if not bar:
                continue
            h, l = bar
            checked += 1
            if not (l <= r["entry"] <= h):
                outside += 1
            elif r["entry"] in (h, l):
                at_extreme += 1
        if checked:
            if outside:
                findings.append(("FAIL", "%d/%d 笔入场价落在该 bar 的 high/low 之外：数据或撮合不真实" % (outside, checked)))
            if at_extreme:
                findings.append(("WARN", "%d/%d 笔入场价正好等于 bar 极值：常见前视/理想化成交痕迹" % (at_extreme, checked)))
            findings.append(("PASS", "价格落在 bar 区间内：%d 笔可比对" % (checked - outside)))
        else:
            findings.append(("NODATA", "OHLC 与交易日期对不上，价格级检查未执行"))
    else:
        findings.append(("UNVERIFIED", "没有 --ohlc：只能查时间戳，价格级前视（用当根 bar 收盘/极值成交）判不了"))

    wins = [r for r in rows if r["pnl"] is not None]
    if len(wins) >= 30:
        k = sum(1 for r in wins if r["pnl"] > 0)
        p = binom_sf(k, len(wins))
        if p < 0.001:
            findings.append(("WARN", "胜率 %d/%d=%.1f%%，二项检验 p=%.1e：先排除前视与幸存者再谈能力" % (k, len(wins), 100.0 * k / len(wins), p)))
    return findings


def _mt_at(per, n, trials):
    """Verdict for one trial count. Returns (verdict, threshold, p_adj, p_one)."""
    z = per * math.sqrt(n)
    p_one = 1.0 - normal_cdf(z)
    if not trials or trials <= 1:
        return None, None, None, p_one
    p_adj = min(1.0, trials * p_one)
    threshold = math.sqrt(2.0 * math.log(trials) / n)
    return ("PASS" if p_adj < 0.05 else "FAIL"), threshold, p_adj, p_one


def check_multiple_testing(returns, ppy, trials, ppy_note, timeframes=1):
    per, mean = sharpe_per_period(returns)
    if per is None:
        return [("NODATA", "收益序列太短或方差为 0，算不出 Sharpe")], {}
    n = len(returns)
    tf = max(1, int(timeframes or 1))
    n_eff = trials * tf if trials else None
    verdict, threshold, p_adj, p_one = _mt_at(per, n, n_eff)
    if verdict is None:
        p_adj = None
        threshold = None
        msg = "没给 --trials：未做多重检验校正（每期 SR %.2f，单次 p=%.2g）；参数网格搜过 N 组就填 N" % (per, p_one)
        if tf > 1:
            msg += "，再乘以 --timeframes %d（你现在只给了时间框架数）" % tf
        findings = [("UNVERIFIED", msg)]
    else:
        if tf > 1:
            msg = "每期 SR %.2f %s 门槛 %.2f（N_eff=%d = 你报的 %d 组 × %d 个时间框架，校正后 p=%.2g）—— %s" % (
                per, ">" if verdict == "PASS" else "<", threshold, n_eff, trials, tf, p_adj,
                "越过「最好的一次尝试」线" if verdict == "PASS" else "与「试了 N_eff 次里最好的那次」不可区分",
            )
        elif verdict == "PASS":
            msg = "每期 SR %.2f > 门槛 %.2f（N=%d，校正后 p=%.2g）—— 越过「最好的一次尝试」线" % (per, threshold, n_eff, p_adj)
        else:
            msg = "每期 SR %.2f < 门槛 %.2f（N=%d，校正后 p=%.2g）—— 与「试了 N 次里最好的那次」不可区分" % (per, threshold, n_eff, p_adj)
        findings = [(verdict, msg)]
        if tf > 1 and trials and trials > 1:
            v_rep, thr_rep, p_rep, _ = _mt_at(per, n, trials)
            if v_rep != verdict:
                findings.append(("WARN", "多尺度搜索膨胀：只按 N=%d 判 %s（门槛 %.2f），把 %d 个时间框架计入后判 %s（门槛 %.2f）—— 每个时间框架上的参数也是一次搜索。" % (
                    trials, v_rep, thr_rep, tf, verdict, threshold)))
    extra = {
        "sharpe_per_period": per,
        "sharpe_annual": per * math.sqrt(ppy),
        "periods": n,
        "ppv_note": ppy_note,
        "p_single": p_one,
        "p_adjusted": p_adj,
        "threshold_per_period": threshold,
        "trials": trials,
        "timeframes": tf,
        "trials_effective": n_eff,
        "multiscale_inflation": bool(tf > 1 and trials and trials > 1),
    }
    return findings, extra


def check_oos(returns, split, ppy):
    n = len(returns)
    if n < 20:
        return [("NODATA", "样本不足 20 期，无法做样本外对照")], {}
    cut = max(5, min(n - 5, int(round(n * split))))
    ins, oos = returns[:cut], returns[cut:]
    sr_in, mean_in = sharpe(ins, ppy)
    sr_out, mean_out = sharpe(oos, ppy)
    if sr_in is None or sr_out is None:
        return [("NODATA", "某一半方差为 0，无法比较")], {}
    decay = 1.0 - (sr_out / sr_in) if sr_in > 0 else None
    if sr_out <= 0:
        verdict = "FAIL"
        msg = "前半 SR %.2f -> 后半 SR %.2f：后半为负，样本外没有留下边" % (sr_in, sr_out)
    elif decay is not None and decay >= 0.5:
        verdict = "WARN"
        msg = "前半 SR %.2f -> 后半 SR %.2f，衰减 %.0f%%：超过一半的边没走到样本外" % (sr_in, sr_out, 100 * decay)
    else:
        verdict = "PASS"
        msg = "前半 SR %.2f -> 后半 SR %.2f（衰减 %s）：后半仍在" % (sr_in, sr_out, "n/a" if decay is None else "%.0f%%" % (100 * decay))
    thirds = [returns[i * n // 3:(i + 1) * n // 3] for i in range(3)]
    signs = [("+" if sum(t) > 0 else "-") for t in thirds if t]
    if "-" in signs:
        msg += "；三段均值符号 %s" % "".join(signs)
    return [(verdict, msg)], {"sharpe_in": sr_in, "sharpe_out": sr_out, "decay": decay, "split_index": cut}


def overall_verdict(findings):
    verdicts = [v for v, _ in findings]
    if "FAIL" in verdicts:
        return "FAIL"
    if "UNVERIFIED" in verdicts:
        return "UNVERIFIED"
    if "WARN" in verdicts:
        return "WARN"
    if "NODATA" in verdicts:
        return "NODATA"
    return "PASS"


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="auditkit",
        description="Three checks on one backtest CSV: look-ahead, multiple testing, out-of-sample decay.",
    )
    ap.add_argument("csv", help="trades or equity CSV")
    ap.add_argument("--ohlc", help="optional bars CSV with date, high, low")
    ap.add_argument("--trials", type=int, default=None, help="how many parameter combos you searched (N)")
    ap.add_argument("--timeframes", type=int, default=1, help="how many time frames you tuned the grid on; multiplies --trials (default 1)")
    ap.add_argument("--split", type=float, default=0.5, help="in-sample fraction (default 0.5)")
    ap.add_argument("--initial", type=float, default=10000.0, help="initial capital if only pnl is present")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    if not os.path.exists(args.csv):
        print("auditkit: no such file: %s" % args.csv, file=sys.stderr)
        return 1
    series = load_series(args.csv)
    if not series or not series["rows"]:
        print("auditkit: empty CSV", file=sys.stderr)
        return 1

    returns, source = build_returns(series, args.initial)
    stamps = [r["ts"] for r in series["rows"]]
    ppy, ppy_note = infer_ppy(stamps)

    la = check_lookahead(series, args.ohlc)
    if args.timeframes < 1:
        ap.error("--timeframes must be >= 1")
    mt, mt_extra = check_multiple_testing(returns, ppy, args.trials, ppy_note, args.timeframes)
    oos, oos_extra = check_oos(returns, args.split, ppy)

    blocks = [("look-ahead", la), ("multiple testing", mt), ("out-of-sample decay", oos)]
    if args.json:
        payload = {
            "file": args.csv,
            "rows": len(series["rows"]),
            "returns_source": source,
            "checks": {name: [{"verdict": v, "detail": d} for v, d in fs] for name, fs in blocks},
            "verdicts": {name: overall_verdict(fs) for name, fs in blocks},
            "stats": {"multiple_testing": mt_extra, "oos": oos_extra, "ppy": ppy, "ppy_note": ppy_note},
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        verdicts = payload["verdicts"].values()
    else:
        print("")
        print("auditkit -- %s  (%d rows, %d return periods, %s)" % (args.csv, len(series["rows"]), len(returns), source))
        print("=" * 78)
        for name, fs in blocks:
            print("")
            print("[%s] %s" % (name, overall_verdict(fs)))
            for v, d in fs:
                print("   %-10s %s" % (v, d))
        print("")
        print("-" * 78)
        print("legend: PASS 过了 / WARN 有痕迹 / FAIL 站不住 / UNVERIFIED 缺输入，判不了 / NODATA 没数据")
        verdicts = [overall_verdict(fs) for _, fs in blocks]

    if "FAIL" in verdicts:
        return 1
    if "UNVERIFIED" in verdicts:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
