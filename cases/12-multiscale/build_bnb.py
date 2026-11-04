"""BNB rule: a -3% day -> long at that close, exit next daily close. 15bp cost."""
import csv, datetime as dt
SRC='/root/.openclaw/workspace/trading_research/data/binance_BNB_daily.csv'
START=1546300800000; DROP=-0.03; COST=0.0015
rows=[(int(float(r['ts'])), float(r['close'])) for r in csv.DictReader(open(SRC))]
rows=[r for r in rows if r[0]>=START]
out=[]; i=1
while i < len(rows)-1:
    r24=rows[i][1]/rows[i-1][1]-1
    if r24<=DROP:
        pnl=rows[i+1][1]/rows[i][1]-1-COST
        d=dt.datetime.fromtimestamp(rows[i][0]/1000, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        out.append({'date':d,'entry_price':round(rows[i][1],4),'exit_price':round(rows[i+1][1],4),
                    'return':round(pnl,6),'trigger_ret24':round(r24,6)})
        i+=2
    else: i+=1
w=csv.DictWriter(open('bnb_trades.csv','w',newline=''),fieldnames=list(out[0].keys()))
w.writeheader(); w.writerows(out)
print('trades',len(out),'span',out[0]['date'],'->',out[-1]['date'])
eq=1.0
for t in out: eq*=1+t['return']
print('total %.1f%%'%(100*(eq-1)))
