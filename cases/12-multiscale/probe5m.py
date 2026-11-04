import csv, gzip, statistics
SRC='/root/.openclaw/workspace/trading_research/data/agg_ETHUSDT_5m.csv.gz'
ts=[];px=[]
with gzip.open(SRC,'rt') as f:
    for r in csv.DictReader(f):
        ts.append(int(r['ts'])); px.append(float(r['last']))
B=288
def run(start_ms, cost=0.0029, drop=-0.02, cooldown=0):
    out=[]; i=B
    while i < len(px)-B:
        if ts[i] < start_ms: i+=1; continue
        ret=px[i]/px[i-B]-1
        if ret<=drop:
            out.append(px[i+B]/px[i]-1-cost)
            i+=B+cooldown
        else: i+=1
    return out
def st(tr):
    if len(tr)<3: return None
    m=statistics.mean(tr); s=statistics.pstdev(tr)
    t=m/(s/len(tr)**0.5) if s else 0
    return len(tr), round(100*m,2), round(100*s,2), round(t,2), round(100*sum(1 for x in tr if x>0)/len(tr),1)
for lbl,start in [('31m',1730332800000),('67m',1620000000000)]:
    for cd in (0,288,1440,2880):
        print(lbl,'cooldown_bars',cd,st(run(start,cooldown=cd)))
