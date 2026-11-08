#!/usr/bin/env python3
"""Download BTCUSDT 1d klines from data.binance.vision (monthly zips) into btc_daily.csv.

No API key, no rate-limit issues: one small zip per month, 8 threads.
"""
import csv, io, json, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request

BASE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/"
MONTHS = [(y, m) for y in range(2019, 2027) for m in range(1, 13)]
MONTHS = [ym for ym in MONTHS if ym <= (2026, 10)]

def one(ym):
    y, m = ym
    name = "BTCUSDT-1d-%04d-%02d.zip" % (y, m)
    try:
        req = Request(BASE + name, headers={"User-Agent": "work-sample/1.0"})
        with urlopen(req, timeout=30) as r:
            blob = r.read()
        z = zipfile.ZipFile(io.BytesIO(blob))
        text = z.read(z.namelist()[0]).decode()
        rows = []
        for line in text.strip().splitlines():
            p = line.split(",")
            if len(p) < 6: continue
            rows.append((int(p[0]), float(p[1]), float(p[4])))
        return rows, None
    except Exception as e:
        return [], "%s: %s" % (name, e)

def main():
    out, errs = [], []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for rows, err in ex.map(one, MONTHS):
            out.extend(rows)
            if err: errs.append(err)
    seen, clean = set(), []
    for r in sorted(out):
        if r[0] in seen: continue
        seen.add(r[0]); clean.append(r)
    with open("btc_daily.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "close"])
        w.writerows(clean)
    print(json.dumps({"rows": len(clean), "errors": len(errs), "first": clean[0][0] if clean else None, "last": clean[-1][0] if clean else None}))
    for e in errs[:3]: print("ERR", e)

if __name__ == "__main__":
    main()