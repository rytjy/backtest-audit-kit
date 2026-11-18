"""Seven judgment cards for trade ledgers (state.json / dump shapes).

Extracted from the standalone auditkit prototype so the published package can
audit live/paper ledgers without changing the CSV path in auditkit.cli.
"""
from __future__ import annotations

import csv
import json
import math
import os
from datetime import datetime

from ..checks import lookahead as la

BPS = 10_000.0
FEE_BPS_SIDE = 4.5
SLIP_BPS_FILL = 2.0
FUNDING_BPS_BAR = 0.0104  # 0.01%/8h spread over a 5-minute bar


def parse_ts(s):
    for fmt in ("%m-%d %H:%M", "%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(str(s), fmt)
        except (ValueError, TypeError):
            continue
    return None


def load_state(path):
    with open(path) as fh:
        return json.load(fh)


def equity_chain(state):
    eq = [float(state.get("capital", 0.0))]
    for t in state.get("trades", []):
        eq.append(eq[-1] + float(t.get("pnl_usdt", 0.0) or 0.0))
    return eq


def max_drawdown(eq):
    peak, mdd = eq[0], 0.0
    for x in eq:
        peak = max(peak, x)
        if peak > 0:
            mdd = max(mdd, (peak - x) / peak)
    return mdd


def signed_move(t):
    a = float(t.get("entry_px", 0) or 0)
    b = float(t.get("exit_px", 0) or 0)
    if a <= 0:
        return 0.0
    m = (b - a) / a
    return m if str(t.get("side", "")).lower() != "short" else -m


def card_identity(state):
    trades = state.get("trades", [])
    cap = float(state.get("capital", 0.0))
    bal = state.get("balance")
    rep_pnl = state.get("total_pnl")
    s = sum(float(t.get("pnl_usdt", 0.0) or 0.0) for t in trades)
    locked = sum(float(v.get("margin", 0) or 0) for v in (state.get("positions") or {}).values())
    rows = [f"trades={len(trades)} sum(pnl_usdt)={s:.4f}",
            f"reported total_pnl={rep_pnl} capital={cap} balance={bal}"]
    fails = []
    if rep_pnl is not None and abs(s - float(rep_pnl)) > 0.01:
        fails.append(f"sum(trades) != total_pnl (diff {s - float(rep_pnl):+.4f})")
    eq_report = float(bal) + locked if bal is not None else None
    if eq_report is not None and abs((cap + (float(rep_pnl) if rep_pnl is not None else s)) - eq_report) > 0.01:
        fails.append(f"capital+total_pnl != balance+locked_margin "
                     f"(diff {cap + (float(rep_pnl) if rep_pnl is not None else s) - eq_report:+.4f})")
    if eq_report is not None:
        rows.append(f"locked margin in open positions={locked:.2f} -> equity={eq_report:.2f}")
    return ("FAIL" if fails else "PASS"), rows + fails, ("账本恒等式不成立" if fails else "本账本自身能对上")


def card_costs(state, fee_bps=FEE_BPS_SIDE):
    trades = state.get("trades", [])
    if not trades:
        return "UNVERIFIED", ["no trades"], "无成交记录"
    charged = sum(float(t.get("fee_paid", 0.0) or 0.0) for t in trades)
    cost = slip = fund = 0.0
    for t in trades:
        notional = float(t.get("margin", 0) or 0) * float(t.get("leverage", 1) or 1)
        cost += 2 * notional * fee_bps / BPS
        slip += 2 * notional * SLIP_BPS_FILL / BPS
        a, b = parse_ts(t.get("entry_time")), parse_ts(t.get("exit_time"))
        bars = max(1, int((b - a).total_seconds() // 300) + 1) if a and b else 1
        fund += notional * FUNDING_BPS_BAR / BPS * bars
    pnl = sum(float(t.get("pnl_usdt", 0.0) or 0.0) for t in trades)
    total = cost + slip + fund
    rows = [f"trades={len(trades)} fee_charged={charged:.2f}",
            f"venue rate {fee_bps}bps/side: fees={cost:.2f} funding={fund:.2f} slippage={slip:.2f} TOTAL={total:.2f}",
            f"paper pnl={pnl:.2f}  cost/pnl={abs(total / pnl) if pnl else float('inf'):.2f}x"]
    if charged == 0 and total > 0:
        return "PASS", rows, "一笔费都没记：账面盈亏是零成本口径"
    if pnl < 0 and total > abs(pnl) * 0.5:
        return "PASS", rows, "成本量级与盈亏同阶"
    return "FAIL", rows, "成本不足以否定该账本"


def card_toll(config, state):
    if not config:
        return "UNVERIFIED", ["no config"], "缺策略配置"
    lev = float(config.get("leverage", 1))
    toll = 2 * FEE_BPS_SIDE / 100
    rows = [f"leverage={lev} round-trip fee toll={toll:.3f}% of notional"]
    worst = None
    for name, a in (config.get("assets") or {}).items():
        tp = float(a.get("take_profit", 0) or 0)
        need = tp / lev
        rows.append(f"{name}: take_profit={tp}% margin -> needs {need:.4f}% price move")
        if worst is None or need < worst:
            worst = need
    if worst is None:
        return "UNVERIFIED", rows, "配置里没有 take_profit"
    if worst <= toll:
        rows.append(f"min target {worst:.4f}% <= toll {toll:.3f}%")
        return "PASS", rows, "止盈目标小于往返过路费：每一笔赢单扣成本后仍是亏的"
    return "FAIL", rows, "目标高于过路费"


def card_mdd(state):
    eq = equity_chain(state)
    rows = [f"equity start={eq[0]:.2f} end={eq[-1]:.2f} min={min(eq):.2f}",
            f"raw_mdd={100*max_drawdown(eq):.2f}%"]
    return "PASS", rows, "按逐笔权益链算的回撤"


def card_sampling(state):
    ts = [parse_ts(t.get("entry_time")) for t in state.get("trades", [])]
    ts = sorted(x for x in ts if x)
    if not ts:
        return "UNVERIFIED", ["no timestamps"], "无时间戳"
    clusters, cur = [], 1
    for a, b in zip(ts, ts[1:]):
        if (b - a).total_seconds() <= 300:
            cur += 1
        else:
            clusters.append(cur)
            cur = 1
    clusters.append(cur)
    big = max(clusters)
    uniq = len(set(x.strftime("%m-%d %H:%M") for x in ts))
    rows = [f"n={len(ts)} unique_entry_minutes={uniq}", f"max trades in a 5-min chain={big}"]
    return ("PASS" if big >= 3 else "FAIL"), rows, "同一事件被拆成多笔则有效样本被高估"


def card_lookahead(code_path):
    if not code_path or not os.path.exists(code_path):
        return "UNVERIFIED", ["no code given"], "未提供策略源码"
    fs = la.detect_file(code_path)
    rows = [f"findings={len(fs)}"] + [f"  line {f.lineno}: {f.message}" for f in fs[:8]]
    return ("PASS" if fs else "FAIL"), rows, ("AST 扫描前视/未来函数" if fs else "未发现前视写法")


def card_numeric(ticks_path, n=2000):
    probe = [100 + 1e-6 * i for i in range(6)]

    def naive(y):
        N = len(y)
        i = list(range(N))
        si, sy = sum(i), sum(y)
        sxy = sum(a * b for a, b in zip(i, y))
        sxx = sum(a * a for a in i)
        syy = sum(b * b for b in y)
        num = N * sxy - si * sy
        den = math.sqrt(max((N * sxx - si * si) * (N * syy - sy * sy), 0.0))
        return float("nan") if den == 0 else (num / den) ** 2

    def centred(y):
        N = len(y)
        m = sum(y) / N
        c = [v - m for v in y]
        mi = (N - 1) / 2
        sxy = sum((a - mi) * b for a, b in zip(range(N), c))
        sxx = sum((a - mi) ** 2 for a in range(N))
        syy = sum(b * b for b in c)
        den = math.sqrt(sxx * syy)
        return float("nan") if den == 0 else (sxy / den) ** 2

    rows, bad = [], 0
    for k in range(2, 7):
        a, b = naive(probe[:k]), centred(probe[:k])
        rows.append(f"probe n={k} naive={a!r} centred={b!r}")
        if b == b and abs(b - 1.0) < 1e-9 and (a != a or abs(a - 1.0) > 0.01):
            bad += 1
    if ticks_path and os.path.exists(ticks_path):
        ys = []
        with open(ticks_path) as fh:
            for i, line in enumerate(csv.DictReader(fh)):
                if i >= n:
                    break
                try:
                    ys.append(float(line["price"]))
                except (KeyError, ValueError):
                    continue
        if len(ys) > 10:
            m = sum(ys) / len(ys)
            var_n = sum(y * y for y in ys) / len(ys) - m * m
            var_c = sum((y - m) ** 2 for y in ys) / len(ys)
            rel = abs(var_n - var_c) / var_c if var_c else float("inf")
            rows.append(f"real ticks n={len(ys)} var_naive={var_n:.6e} var_centred={var_c:.6e} relerr={100*rel:.4f}%")
    return ("PASS" if bad else "FAIL"), rows, ("原始矩公式在共线序列上偏离 1.0" if bad else "未复现")
