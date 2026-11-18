"""Batch audit — run the judgment cards over many ledgers in one pass.

    python3 -m auditkit batch manifest.json [--out report.md] [--json]

Manifest shape::

    {"jobs": [
      {"name": "paper-2026-06-03", "state": "/root/paper_trade_state_backup.json",
       "config": "strategy.json", "code": "strat.py", "ticks": "btc_ticks.csv"},
      ...
    ]}

Two input shapes are understood:

* **ledger state** — trades carry pnl_usdt / margin / leverage / entry_px /
  exit_px (the shape auditkit run consumes);
* **dump** — {"trades": [{entry_notional, holding_bars, ...}], "ledger": [{bar, cap, ...}]}
  produced by the older backtest dumps.

A card whose inputs are absent reports UNVERIFIED instead of guessing.
Batch raises throughput, not the hit rate: the same seven rules are applied to
more datasets, and every number still has to be readable from the file.
"""
from __future__ import annotations

import json
import os
import sys
import time

from .cards import (
    BPS,
    FEE_BPS_SIDE,
    SLIP_BPS_FILL,
    FUNDING_BPS_BAR,
    card_costs,
    card_identity,
    card_lookahead,
    card_mdd,
    card_numeric,
    card_sampling,
    card_toll,
    equity_chain,
    load_state,
    max_drawdown,
)

CARDS = ("identity", "drawdown", "sampling", "costs", "lookahead", "numeric", "toll")
CARD_LABEL = {
    "identity": "账本恒等",
    "drawdown": "回撤",
    "sampling": "样本膨胀",
    "costs": "成本",
    "lookahead": "前视",
    "numeric": "数值",
    "toll": "过路费",
}
# Map the cards' PASS/FAIL vocabulary onto one that reads the same in a table.
VERDICT_MAP = {
    "identity": {"PASS": "ok", "FAIL": "broken", "UNVERIFIED": "unverified"},
    "drawdown": {"PASS": "measured", "FAIL": "measured", "UNVERIFIED": "unverified"},
    "sampling": {"PASS": "hit", "FAIL": "clean", "UNVERIFIED": "unverified"},
    "costs": {"PASS": "hit", "FAIL": "clean", "UNVERIFIED": "unverified"},
    "lookahead": {"PASS": "hit", "FAIL": "clean", "UNVERIFIED": "unverified"},
    "numeric": {"PASS": "hit", "FAIL": "clean", "UNVERIFIED": "unverified"},
    "toll": {"PASS": "hit", "FAIL": "clean", "UNVERIFIED": "unverified"},
}


def _dump_equity(state):
    return [float(row.get("cap", 0.0) or 0.0) for row in (state.get("ledger") or [])]


def _dump_costs(state, fee_bps=FEE_BPS_SIDE, slip_bps=SLIP_BPS_FILL, funding_bps_bar=FUNDING_BPS_BAR):
    trades = state.get("trades") or []
    if not trades:
        return "UNVERIFIED", ["no trades"], "无成交记录"
    charged = sum(float(t.get("fee_paid", 0.0) or 0.0) for t in trades)
    fees = slip = fund = 0.0
    for t in trades:
        notional = float(t.get("entry_notional", 0.0) or 0.0)
        fees += 2 * notional * fee_bps / BPS
        slip += 2 * notional * slip_bps / BPS
        bars = max(1, int(t.get("holding_bars", 1) or 1))
        fund += notional * funding_bps_bar / BPS * bars
    total = fees + slip + fund
    rows = [
        f"trades={len(trades)} fee_charged={charged:.2f}",
        f"venue rate {fee_bps}bps/side: fees={fees:.2f} funding={fund:.2f} slippage={slip:.2f} TOTAL={total:.2f}",
    ]
    if charged == 0 and total > 0:
        return "PASS", rows, "一笔费都没记：账面是零成本口径"
    return "FAIL", rows, "已记费用，成本未由零起算"


def _toll_from_config(config):
    """Card 7 only needs take_profit/leverage, so it works for dump inputs too."""
    if not config:
        return "UNVERIFIED", ["no config"], "缺策略配置"
    lev = float(config.get("leverage", 1) or 1)
    toll = 2 * FEE_BPS_SIDE / 100
    worst = None
    rows = [f"leverage={lev} round-trip fee toll={toll:.3f}% of notional"]
    for name, a in (config.get("assets") or {}).items():
        tp = float(a.get("take_profit", 0) or 0)
        need = tp / lev if lev else 0.0
        rows.append(f"{name}: take_profit={tp}% margin -> needs {need:.4f}% price move")
        worst = need if worst is None or need < worst else worst
    if worst is None:
        return "UNVERIFIED", rows, "配置里没有 take_profit"
    if worst <= toll:
        rows.append(f"min target {worst:.4f}% <= toll {toll:.3f}%")
        return "PASS", rows, "止盈目标小于往返过路费：每笔赢单扣成本后仍是亏的"
    return "FAIL", rows, "目标高于过路费"


def _audit_ledger(state, job):
    config = load_state(job["config"]) if job.get("config") else None
    raw = {
        "identity": card_identity(state),
        "drawdown": card_mdd(state),
        "sampling": card_sampling(state),
        "costs": card_costs(state),
        "lookahead": card_lookahead(job.get("code")),
        "numeric": card_numeric(job.get("ticks")),
        "toll": card_toll(config, state),
    }
    return raw, equity_chain(state)


def _audit_dump(state, job):
    equity = _dump_equity(state)
    if len(equity) >= 2:
        mdd_rows = [
            f"equity start={equity[0]:.2f} end={equity[-1]:.2f} min={min(equity):.2f}",
            f"raw_mdd={100 * max_drawdown(equity):.2f}%",
        ]
        drawdown = ("PASS", mdd_rows, "按账本 cap 序列算的回撤")
    else:
        drawdown = ("UNVERIFIED", ["no ledger bars"], "缺账本序列")
    config = load_state(job["config"]) if job.get("config") else None
    raw = {
        "identity": ("UNVERIFIED", ["dump 无 balance/total_pnl 字段"], "该形状不提供账本恒等字段"),
        "drawdown": drawdown,
        "sampling": ("UNVERIFIED", ["dump 无 entry 时间戳"], "该形状不提供入场时间"),
        "costs": _dump_costs(state),
        "lookahead": card_lookahead(job.get("code")),
        "numeric": card_numeric(job.get("ticks")),
        "toll": _toll_from_config(config),
    }
    return raw, equity


def audit_one(job):
    started = time.perf_counter()
    path = job["state"]
    state = load_state(path)
    kind = "dump" if state.get("ledger") else "ledger"
    raw, equity = _audit_ledger(state, job) if kind == "ledger" else _audit_dump(state, job)
    if not job.get("ticks"):
        _, probe_rows, _ = raw["numeric"]
        raw["numeric"] = (
            "UNVERIFIED",
            list(probe_rows) + ["no ticks given"],
            "未提供 ticks：内置探针结果不代表该数据集",
        )
    cards = {}
    for name in CARDS:
        verdict, rows, why = raw[name]
        cards[name] = {
            "verdict": VERDICT_MAP[name].get(verdict, verdict.lower()),
            "raw": verdict,
            "rows": rows,
            "why": why,
        }
    pnl = (equity[-1] - equity[0]) if len(equity) >= 2 else None
    cost_row = next((r for r in cards["costs"]["rows"] if "TOTAL=" in r), "")
    total_cost = None
    if "TOTAL=" in cost_row:
        try:
            total_cost = float(cost_row.split("TOTAL=")[1].split()[0])
        except (IndexError, ValueError):
            total_cost = None
    return {
        "name": job.get("name") or os.path.basename(path),
        "path": os.path.abspath(path),
        "kind": kind,
        "trades": len(state.get("trades") or []),
        "equity_start": equity[0] if equity else None,
        "equity_end": equity[-1] if equity else None,
        "pnl": pnl,
        "mdd": (max_drawdown(equity) if len(equity) >= 2 else None),
        "cost_total": total_cost,
        "cards": cards,
        "seconds": round(time.perf_counter() - started, 3),
    }


def _fmt(x, digits=2, suffix=""):
    if x is None:
        return "—"
    return f"{x:,.{digits}f}{suffix}"


def render_markdown(results):
    hits = {name: 0 for name in CARDS}
    unverified = {name: 0 for name in CARDS}
    for r in results:
        for name, card in r["cards"].items():
            if card["verdict"] == "hit":
                hits[name] += 1
            elif card["verdict"] == "unverified":
                unverified[name] += 1
    lines = [
        f"## 批量审计 · {len(results)} 个数据集",
        "",
        "| # | 数据集 | 形状 | 笔数 | 期末权益 | 盈亏 | MDD | 估算成本 | 成本/|盈亏| | 命中卡 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        ratio = None
        if r["pnl"] not in (None, 0) and r["cost_total"] is not None:
            ratio = abs(r["cost_total"] / r["pnl"])
        hit_names = [CARD_LABEL[n] for n, c in r["cards"].items() if c["verdict"] == "hit"]
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                i,
                r["name"],
                "dump" if r["kind"] == "dump" else "ledger",
                r["trades"],
                _fmt(r["equity_end"]),
                _fmt(r["pnl"], 2),
                _fmt(None if r["mdd"] is None else 100 * r["mdd"], 1, "%"),
                _fmt(r["cost_total"]),
                "—" if ratio is None else f"{ratio:.2f}x",
                "、".join(hit_names) if hit_names else "—",
            )
        )
    lines += [
        "",
        "图例：**命中** = 该卡判定缺陷成立（PASS）；未列出的卡为「未成立」或「未测」。"
        "dump 形状没有 balance / entry 时间戳，对应卡一律标未测，不做推断。",
        "",
        "### 逐卡覆盖",
        "",
        "| 卡 | 命中 | 未测 |",
        "|---|---|---|",
    ]
    for name in CARDS:
        lines.append(f"| {CARD_LABEL[name]} | {hits[name]} | {unverified[name]} |")
    total_s = sum(r["seconds"] for r in results)
    med = sorted(r["seconds"] for r in results)[len(results) // 2]
    lines += [
        "",
        f"耗时合计 {total_s:.2f}s；单数据集中位 {med:.2f}s。",
        "",
        "> 范围声明：批量只提高吞吐，不提高单靶命中率。所有数字来自输入文件；"
        "缺字段的卡标「未测」，未用默认值补齐。",
    ]
    return "\n".join(lines)


def cmd_batch(manifest_path, out_path=None, as_json=False):
    manifest = load_state(manifest_path)
    jobs = manifest.get("jobs") or []
    if not jobs:
        print("manifest has no jobs", file=sys.stderr)
        return 2
    base = os.path.dirname(os.path.abspath(manifest_path))
    for job in jobs:
        p = job.get("state")
        if p and not os.path.isabs(p):
            job["state"] = os.path.join(base, p)
        for key in ("config", "code", "ticks"):
            v = job.get(key)
            if v and not os.path.isabs(v):
                job[key] = os.path.join(base, v)
    results = [audit_one(job) for job in jobs]
    report = render_markdown(results)
    print(report)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
        print(f"\nwrote {out_path}")
    if as_json:
        print(json.dumps({"jobs": results}, ensure_ascii=False, indent=1))
    return 0
