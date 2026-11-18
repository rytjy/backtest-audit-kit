"""CLI for ledger audits: one ledger, or a batch manifest.

    python3 -m auditkit.ledger run state.json --config strategy.json
    python3 -m auditkit.ledger batch examples/ledger/manifest.json --out report.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .batch import cmd_batch
from .sweep import cmd_sweep
from .cards import (
    card_costs,
    card_identity,
    card_lookahead,
    card_mdd,
    card_numeric,
    card_sampling,
    card_toll,
    load_state,
)


def _run(state_path, config_path, code_path, ticks_path, as_json):
    state = load_state(state_path)
    config = load_state(config_path) if config_path else None
    cards = [
        ("1 look-ahead", card_lookahead(code_path)),
        ("2 ledger identity", card_identity(state)),
        ("3 drawdown", card_mdd(state)),
        ("4 sample inflation", card_sampling(state)),
        ("5 costs vs toll", card_costs(state)),
        ("6 numeric (R^2)", card_numeric(ticks_path)),
        ("7 take-profit vs toll", card_toll(config, state)),
    ]
    out = {"file": os.path.abspath(state_path), "cards": {}}
    print("=" * 72)
    print(f"auditkit.ledger run  {state_path}")
    print("=" * 72)
    default_label = {"PASS": "PASS 缺陷成立", "FAIL": "FAIL 未成立", "UNVERIFIED": "UNVERIFIED 未测"}
    per_card = {
        "2 ledger identity": {"PASS": "PASS 账本一致", "FAIL": "FAIL 恒等式不成立"},
        "3 drawdown": {"PASS": "PASS 已测量", "FAIL": "FAIL 已测量"},
    }
    for name, (verdict, rows, why) in cards:
        label = per_card.get(name, default_label)
        print(f"\n[{label.get(verdict, verdict)}] card {name}")
        for row in rows:
            print("   " + row)
        print("   -> " + why)
        out["cards"][name] = {"verdict": verdict, "rows": rows, "why": why}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="auditkit.ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="audit one trade ledger")
    run.add_argument("state")
    run.add_argument("--config")
    run.add_argument("--code")
    run.add_argument("--ticks")
    run.add_argument("--json", action="store_true")
    bt = sub.add_parser("batch", help="audit many ledgers from a manifest")
    bt.add_argument("manifest")
    bt.add_argument("--out", help="write the markdown report here")
    bt.add_argument("--json", action="store_true")
    sw = sub.add_parser("sweep", help="cost sensitivity over take-profit and leverage")
    sw.add_argument("state")
    sw.add_argument("--config")
    sw.add_argument("--grid", default="1.5,3,5,8,10,15,26")
    sw.add_argument("--leverage", default="20,40,50,100")
    args = ap.parse_args(argv)

    if args.cmd == "batch":
        return cmd_batch(args.manifest, out_path=args.out, as_json=args.json)
    if args.cmd == "sweep":
        cfg = load_state(args.config) if args.config else None
        return cmd_sweep(load_state(args.state), cfg,
                         [float(x) for x in args.grid.split(",")],
                         [int(x) for x in args.leverage.split(",")])
    return _run(args.state, args.config, args.code, args.ticks, args.json)


if __name__ == "__main__":
    sys.exit(main())
