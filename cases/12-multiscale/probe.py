import csv, datetime as dt, statistics
SRC='/root/.openclaw/workspace/trading_research/data/binance_ETH_daily.csv'
rows=[(int(r['ts']),float(r['close'])) for r in csv.DictReader(open(SRC))]
def run(start_ts, drop=-0.02, cost=0.0029, cooldown_days=1):
    out=[]; i=1
    while i < len(rows)-1:
        if rows[i][0] < start_ts: i+=1; continue
        ret=rows[i][1]/rows[i-1][1]-1
        if ret<=drop:
            pnl=rows[i+1][1]/rows[i][1]-1-cost
            out.append(pnl); i+=1+cooldown_days
        else: i+=1
    return out
def stats(tr):
    if len(tr)<3: return None
    m=statistics.mean(tr); s=statistics.pstdev(tr)
    return len(tr), 100*m, 100*s, (m/s if s else 0), 100*sum(1 for t in tr if t>0)/len(tr)
for label, start in [('31m', 1730332800000), ('36m', 1698796800000), ('24m', 1761868800000)]:
    for cd in (0,1,2,6):
        st=stats(run(start, cooldown_days=cd))
        print(label,'cooldown',cd,'->',st)
