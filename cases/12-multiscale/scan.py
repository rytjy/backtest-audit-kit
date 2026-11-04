import csv, statistics
def load(p):
    return [(int(r['ts']), float(r['close'])) for r in csv.DictReader(open(p))]
def series(path, start=0, cost=0.0015, drop=-0.02, hold=1):
    rows=[r for r in load(path) if r[0]>=start]
    out=[]; i=1
    while i < len(rows)-hold:
        ret=rows[i][1]/rows[i-1][1]-1
        if ret<=drop:
            out.append(rows[i+hold][1]/rows[i][1]-1-cost); i+=1+hold
        else: i+=1
    return out
def st(tr):
    if len(tr)<10: return None
    m=statistics.mean(tr); s=statistics.pstdev(tr)
    return len(tr), round(100*m,2), round(m/(s/len(tr)**0.5),2)
base='/root/.openclaw/workspace/trading_research/data/'
for coin in ['BTC','ETH','SOL']:
    for start in [0, 1546300800000, 1672531200000]:
        for drop in [-0.015,-0.02,-0.025,-0.03]:
            for hold in (1,2,3):
                r=st(series(base+'binance_%s_daily.csv'%coin, start, drop=drop, hold=hold))
                if r and r[0]>=40 and r[2] and 1.9<=r[2]<=2.7:
                    print(coin,start,drop,hold,r)
