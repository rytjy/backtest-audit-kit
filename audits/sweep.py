#!/usr/bin/env python3
"""Fixed target/stop sweep over the public mr-scrooge-v6 live trade log."""
import csv,glob,datetime as dt,bisect,statistics as st,math,sys

PAIRS=['EUR_USD','GBP_USD','USD_JPY']
DATA_DIR=sys.argv[1] if len(sys.argv)>1 else './m1'
CSV_PATH=sys.argv[2] if len(sys.argv)>2 else './trades_detail_2026-10-28.csv'

def load(pair):
    bars={}
    for fp in sorted(glob.glob(DATA_DIR+'/'+pair.replace('_','').lower()+'-*.csv')):
        for line in open(fp):
            try:
                ts,o,h,l,c,v=line.strip().split(';')
                # HistData ASCII M1 timestamps are New York time; +4h = UTC for Jul-Oct (EDT)
                bars[dt.datetime.strptime(ts,'%Y%m%d %H%M%S')+dt.timedelta(hours=4)]=(float(o),float(h),float(l),float(c))
            except Exception:
                pass
    return bars

data={p:load(p) for p in PAIRS}
trades=[t for t in csv.DictReader(open(CSV_PATH)) if t['instrument'] in data]
sel=[]
for t in trades:
    p=t['instrument']; ks=sorted(data[p])
    if not ks: continue
    ts=dt.datetime.strptime(t['open_utc'],'%Y-%m-%dT%H:%M:%SZ')
    i=bisect.bisect_left(ks,ts)
    if i<len(ks): sel.append((t,p,ks,i))

def sim(t,p,ks,i,sm,tm,cap_h=72):
    pip=0.01 if p.endswith('JPY') else 0.0001
    o=float(t['open_price']); R=abs(o-float(t['initial_stop'])); d=t['direction']
    if R<=0: return None
    sl=o-sm*R if d=='long' else o+sm*R
    tp=o+tm*R if d=='long' else o-tm*R
    end=ks[i]+dt.timedelta(hours=cap_h)
    for k in ks[i:]:
        if k>end:
            c=data[p][k][3]
            return ((c-o) if d=='long' else (o-c))/pip
        hi,lo=data[p][k][1],data[p][k][2]
        if (lo<=sl if d=='long' else hi>=sl): return -(sm*R)/pip
        if (hi>=tp if d=='long' else lo<=tp): return (tm*R)/pip
    return 0.0

print('replayable trades: %d of %d'%(len(sel),len(trades)))
print('stop\\target   '+'  '.join('%7.2fR'%tm for tm in [0.5,0.75,1.0,1.5,2.0,3.0]))
for sm in [0.75,1.0,1.25]:
    cells=[]
    for tm in [0.5,0.75,1.0,1.5,2.0,3.0]:
        v=[sim(t,p,ks,i,sm,tm) for t,p,ks,i in sel]; v=[x for x in v if x is not None]
        cells.append('%+7.2f'%st.mean(v))
    print('%.2fR         '%sm+'  '.join(cells))

# full-tape pips vs dollars
allr=list(csv.DictReader(open(CSV_PATH)))
print('full tape: n=%d mean_pips=%+.2f mean_usd=%+.2f'%(
    len(allr), st.mean(float(x['pips']) for x in allr), st.mean(float(x['realized_usd']) for x in allr)))
