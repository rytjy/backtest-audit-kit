#!/usr/bin/env python3
"""Case 7 repro: verify a vault's headline APY against realized share-price growth.

ERC4626 only. Standard library, no install, no API key.

    python3 cases/repro_case7_yield.py --vault 0x... --reported 3.80
    python3 cases/repro_case7_yield.py --vault 0xF9bd... --reported 8.4368 --rpc URL
"""
import argparse
import datetime
import json
import urllib.request

DEFAULT_RPC = "https://gateway.tenderly.co/public/mainnet"
UA = "Mozilla/5.0 (backtest-audit-kit case7)"

def rpc(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"content-type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.loads(r.read().decode())
    if "error" in d:
        raise RuntimeError(d["error"])
    return d["result"]

def as_int(hexstr):
    return int(hexstr, 16) if hexstr and hexstr != "0x" else 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--reported", type=float, default=None)
    ap.add_argument("--rpc", default=DEFAULT_RPC)
    a = ap.parse_args()
    R, V = a.rpc, a.vault

    latest = as_int(rpc(R, "eth_blockNumber", []))
    asset = "0x" + rpc(R, "eth_call", [{"to": V, "data": "0x38d52e0f"}, "latest"])[-40:]
    adec = as_int(rpc(R, "eth_call", [{"to": asset, "data": "0x313ce567"}, "latest"]))
    sdec = as_int(rpc(R, "eth_call", [{"to": V, "data": "0x313ce567"}, "latest"]))

    def pps(block):
        data = "0x07a2d13a" + format(10 ** sdec, "064x")
        return as_int(rpc(R, "eth_call", [{"to": V, "data": data}, hex(block)]))

    def ts(block):
        return int(rpc(R, "eth_getBlockByNumber", [hex(block), False])["timestamp"], 16)

    p_now, t_now = pps(latest), ts(latest)
    print("vault=%s asset=%s asset_decimals=%d share_decimals=%d latest_block=%d"
          % (V, asset, adec, sdec, latest))
    print("pps_now=%.8f assets_per_share" % (p_now / 10 ** adec))
    if a.reported is not None:
        print("reported_apy=%.4f%%" % a.reported)
    print("window  block       utc_date    pps_assets     realized_apy")
    for days in (7, 30, 90, 180):
        b = latest - int(days * 7200)
        try:
            p, t = pps(b), ts(b)
            apy = ((p_now / p) ** (365.25 * 86400 / (t_now - t)) - 1) * 100
            d = datetime.datetime.fromtimestamp(t, datetime.UTC).date()
            print("%4dd   %d  %s  %.8f  %8.4f%%" % (days, b, d, p / 10 ** adec, apy))
        except Exception as e:
            print("%4dd   %d  ERROR %s" % (days, b, str(e)[:120]))

    ta = as_int(rpc(R, "eth_call", [{"to": V, "data": "0x01e1d114"}, "latest"]))
    su = as_int(rpc(R, "eth_call", [{"to": V, "data": "0x18160ddd"}, "latest"]))
    print("totalAssets=%.2f shares=%.2f pps=%.8f"
          % (ta / 10 ** adec, su / 10 ** sdec, (ta / su if su else 0)))

if __name__ == "__main__":
    main()
