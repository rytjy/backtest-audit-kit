import csv, statistics
def load(p): return [(int(float(r['ts'])), float(r['close'])) for r in csv.DictReader(open(p))]
def series(path, start, cost=0.0015, drop=-0.02, hold=1):
    rows=[r for r in load(path) if r[0]>=start]
    out=[]; i=1
    while i < len(rows)-hold:
        if rows[i][1]/rows[i-1][1]-1 <= drop:
            out.append(rows[i+hold][1]/rows[i][1]-1-cost); i+=1+hold
        else: i+=1
    return out
def st(tr):
    if len(tr)<40: return None
    m=statistics.mean(tr); s=statistics.pstdev(tr)
    return len(tr), round(100*m,2), round(m/(s/len(tr)**0.5),2)
base='/root/.openclaw/workspace/trading_research/data/'
best=[]
for coin in ['BTC','ETH','SOL','BNB','XRP','DOGE','LINK','AVAX']:
    for start in [0, 1546300800000, 1672531200000]:
        for drop in [-0.01,-0.015,-0.02,-0.025,-0.03,-0.04]:
            for hold in (1,2,3,5):
                r=st(series(base+'binance_%s_daily.csv'%coin, start, drop=drop, hold=hold))
                if r: best.append((r[2], coin, start, drop, hold, r))
best.sort(reverse=True)
for b in best[:8]: print(b)
