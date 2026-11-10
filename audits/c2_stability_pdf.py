#!/usr/bin/env python3
"""Render the C2 rank-stability table to a 2-page PDF, stdlib only (base-14 fonts).

    python3 scripts/c2_stability_pdf.py loo_result.json out.pdf
"""
import json, sys

W, H = 595.28, 841.89
ML, MR, MT, MB = 48, 48, 52, 44
DARK=(0.25,0.25,0.25); GRAY=(0.45,0.45,0.45)


def esc(s):
    return str(s).replace('\\','\\\\').replace('(','\\(').replace(')','\\)')


def wrap(text, width, size, factor=0.5):
    maxc = max(10, int(width/(size*factor)))
    out, cur = [], ''
    for w in str(text).split():
        t = (cur+' '+w).strip()
        if len(t) <= maxc: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out


class Page:
    def __init__(self, n):
        self.n = n; self.ops = []
    def text(self, x, y, s, size=9, font='F1', color=None):
        if color: self.ops.append('%.3f %.3f %.3f rg' % color)
        self.ops.append('BT /%s %.2f Tf %.2f %.2f Td (%s) Tj ET' % (font, size, x, y, esc(s)))
        if color: self.ops.append('0 0 0 rg')
    def line(self, x1,y1,x2,y2,w=0.5,gray=0.0):
        self.ops.append('%.2f G %.2f w %.2f %.2f m %.2f %.2f l S 0 G'%(gray,w,x1,y1,x2,y2))
    def box(self, x,y,w,h,gray=0.94):
        self.ops.append('%.2f g %.2f %.2f %.2f %.2f re f 0 g'%(gray,x,y,w,h))
    def stream(self):
        return '\n'.join(self.ops).encode('latin-1','replace')


COLS = [('id',74,0),('n',26,1),('ann%',42,1),('base',32,1),('worst',36,1),('drop',30,1),('min ann%',46,1),('month out',52,0),('that mo %',44,1),('best',30,1)]
ROW_H = 15.2

def table_header(p, y):
    x = ML
    p.line(ML, y+11, W-MR, y+11, 0.4, 0.55)
    for name,w,al in COLS:
        if al: p.text(x+w-6-len(name)*4.2, y, name, 7.6, 'F2', DARK)
        else: p.text(x+1, y, name, 7.6, 'F2', DARK)
        x += w
    p.line(ML, y-4, W-MR, y-4, 0.4, 0.55)
    return y-15


def table_row(p, y, r):
    vals = [r['id'], str(r['n']), '%.1f'%r['ann'], str(r['base']), str(r['worst']),
            ('+%d'%(r['worst']-r['base']) if r['worst']!=r['base'] else '0'), '%.1f'%r.get('min', r['ann']),
            '%d-%02d'%(r['wmonth'][0],r['wmonth'][1]),
            '%+.1f'%r['wr'], str(r['best'])]
    x = ML
    for (name,w,al),v in zip(COLS,vals):
        if al: p.text(x+w-6-len(v)*4.05, y, v, 8.3)
        else: p.text(x+1, y, v, 8.3)
        x += w
    p.line(ML, y-4.5, W-MR, y-4.5, 0.25, 0.88)
    return y-ROW_H


def footer(p):
    p.line(ML, MB-10, W-MR, MB-10, 0.3, 0.8)
    p.text(ML, MB-21, 'github.com/rytjy/backtest-audit-kit  |  docs/c2-screen-37.md  |  pages cached 2026-11-07', 7.2, 'F1', GRAY)
    p.text(W-MR-32, MB-21, '%d / 2'%p.n, 7.6, 'F1', GRAY)


def build(rows):
    pages = []
    p = Page(1); pages.append(p)
    y = H-MT
    p.text(ML, y-4, 'Rank stability: 36 Collective2 strategies, one month left out', 15.5, 'F2')
    y -= 22
    p.text(ML, y, 'Companion to docs/c2-screen-37.md  |  2026-11-10  |  every ranking number recomputed from the monthly cells', 8.4, 'F1', GRAY)
    y -= 14
    p.line(ML, y, W-MR, y, 0.8)
    y -= 16
    p.text(ML, y, 'METHOD', 7.8, 'F2', GRAY); y -= 11
    for ln in wrap("Ranking = annualised return from each strategy's monthly cells, eq^(365/days)-1, days = asOf minus the strategy-began date. For each of the 36 active strategies, one month is removed at a time, the remaining record re-annualised over its actual days, the whole set re-ranked, and the worst place that strategy holds across its own months recorded. Baseline is the published ranking.", W-ML-MR, 8.8):
        p.text(ML, y, ln, 8.8); y -= 11.4
    y -= 8
    p.text(ML, y, 'HEADLINE', 7.8, 'F2', GRAY); y -= 11
    heads = [
      'Median worst place: 4 ranks below the current one. Six of 36 fall 10+ places; the largest drop is 15.',
      '25 of 36 touch rank 20 or worse at least once. Four never leave the top 10: 150377786, 141710744, 148705494, 150004796.',
      'Concentration and rank-dependence agree: the 19 flagged above 70% in the best three months have a median worst drop of 7 places; the other 17, 2 places.',
      'Worst single-month cases: 153432780 #8 to #23 without 2026-01 (+30.2%); 153416579 #15 to #29 without 2026-03 (+18.3%).',
      'Rank and return part ways: the four that never leave the top 10 still lose 18.0 to 43.4 points of annualised return on a single omission; the smallest shortfall in the set, 13202557 at 1.0 point, belongs to the strategy ranked #28.',
    ]
    for h in heads:
        for i,ln in enumerate(wrap(h, W-ML-MR-10, 8.8)):
            p.text(ML+(0 if i else 3), y, ('- ' if i==0 else '   ')+ln if i==0 else '   '+ln, 8.8); y -= 11.4
        y -= 1.5
    y -= 8
    p.text(ML, y, 'DETAIL  (sorted by worst place; drop = worst minus baseline, in ranks; min ann% = lowest annualised return when one month is removed)', 7.8, 'F2', GRAY)
    y = table_header(p, y-12)
    for r in rows:
        if y < MB+46:
            footer(p); p = Page(2); pages.append(p); y = H-MT
            p.text(ML, y, 'Rank stability, continued', 11, 'F2'); y -= 8
            p.text(ML, y, 'same method and set', 8.2, 'F1', GRAY); y -= 14
            y = table_header(p, y)
        y = table_row(p, y, r)
    y -= 10
    lim = [
      'One-sided test: removing a positive month can only lower an annualised return, so this measures how much of a place rests on the best month, not symmetric robustness.',
      'Rank runs on annualised return only; ranking by return/drawdown would reorder the set.',
      '146629969 and 150565426 lack begin/asOf dates on the cached page and were annualised by inverting the published annual return.',
      'Set: 37 published ids, one inactive (124293346), 36 active. The leaderboard is a selection - delisted strategies are not measured.',
    ]
    lines = []
    for s in lim: lines += wrap(s, W-ML-MR-16, 8.2)
    bh = 18+10.5*len(lines)
    if y-bh < MB+20:
        footer(p); p = Page(2); pages.append(p); y = H-MT; p.text(ML,y,'Rank stability, continued',11,'F2'); y-=20
    p.box(ML, y-bh, W-ML-MR, bh)
    p.text(ML+8, y-12, 'SCOPE AND LIMITS', 7.6, 'F2', DARK)
    yy = y-23
    for ln in lines:
        p.text(ML+8, yy, ln, 8.2); yy -= 10.5
    footer(p)

    objs = [b'<< /Type /Catalog /Pages 2 0 R >>']
    kids = ' '.join('%d 0 R'%(3+2*i) for i in range(len(pages)))
    objs.append(('<< /Type /Pages /Kids [%s] /Count %d >>'%(kids,len(pages))).encode())
    for i,pg in enumerate(pages):
        objs.append(('<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>'%(W,H,3+2*len(pages),4+2*len(pages),4+2*i)).encode())
        objs.append(b'<< /Length '+str(len(pg.stream())).encode()+b' >>\nstream\n'+pg.stream()+b'\nendstream')
    objs.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    objs.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
    out = bytearray(b'%PDF-1.4\n'); offs=[]
    for i,o in enumerate(objs,1):
        offs.append(len(out)); out += str(i).encode()+b' 0 obj\n'+o+b'\nendobj\n'
    xref=len(out)
    out += ('xref\n0 %d\n'%(len(objs)+1)).encode()+b'0000000000 65535 f \n'
    for o in offs: out += ('%010d 00000 n \n'%o).encode()
    out += ('trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n'%(len(objs)+1,xref)).encode()
    return bytes(out)


if __name__ == '__main__':
    rows = json.load(open(sys.argv[1]))
    rows.sort(key=lambda r: -r['worst'])
    pdf = build(rows)
    open(sys.argv[2],'wb').write(pdf)
    print('wrote', sys.argv[2], len(pdf), 'bytes')
