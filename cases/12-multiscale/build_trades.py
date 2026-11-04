"""Reproduce the ETH 24h-drop rule as a plain trades CSV (daily bars).

Rule: on a daily close, if the trailing 24h return <= -2%, go long 1x at that
close and exit at the next daily close. One position at a time, no pyramiding.
Cost 29bp round trip (taker both sides + slippage).
Data: Binance ETH/USDT daily klines from 2017-08 to 2026-08.
"""
import csv, datetime as dt

SRC = '/root/.openclaw/workspace/trading_research/data/binance_ETH_daily.csv'
COST, DROP = 0.0029, -0.02

rows = []
with open(SRC) as f:
    for r in csv.DictReader(f):
        rows.append((int(r['ts']), float(r['close'])))

trades = []
i = 1
while i < len(rows) - 1:
    ret24 = rows[i][1] / rows[i - 1][1] - 1.0
    if ret24 <= DROP:
        entry, exit_ = rows[i][1], rows[i + 1][1]
        pnl = exit_ / entry - 1.0 - COST
        d = dt.datetime.fromtimestamp(rows[i][0] / 1000, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        trades.append({'date': d, 'entry_price': round(entry, 2), 'exit_price': round(exit_, 2),
                       'return': round(pnl, 6), 'trigger_ret24': round(ret24, 6)})
        i += 2
    else:
        i += 1

with open('trades.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['date', 'entry_price', 'exit_price', 'return', 'trigger_ret24'])
    w.writeheader(); w.writerows(trades)

wins = sum(1 for t in trades if t['return'] > 0)
eq = 1.0
for t in trades: eq *= 1 + t['return']
print('trades', len(trades), 'wins', wins, 'winrate %.1f%%' % (100.0*wins/max(1,len(trades))))
print('span', trades[0]['date'], '->', trades[-1]['date'])
print('total return %.1f%%' % (100*(eq-1)))
