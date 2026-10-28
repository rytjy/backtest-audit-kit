#!/usr/bin/env python3
"""Recompute Collective2 headline metrics from a page's own summary fields.

Input: the five numbers a public C2 strategy page shows -- annual return
(compounded), max drawdown, profit factor, % profitable, average win, average
loss. Output: Calmar and profit factor recomputed from those fields, and the
ratio page/recomputed.

Standard definitions used here:
  Calmar        = annualized return / max drawdown
  Profit factor = (win% * avg win) / ((1 - win%) * avg loss)

If a page's Calmar is not reproducible from its own return and drawdown under
this definition, the page is using a different numerator or denominator than
the label implies. The ratio column tells you whether a single correction
factor would fix it (it does not, in the sample below).
"""
ROWS = [
    # id, ann_ret_pct, max_dd_pct, pf_page, win_pct, avg_win, avg_loss, calmar_page
    ("131145247", 32.4, 14.1, 1.50, 35.6, 903.0, 342.0, 3.52),
    ("132169961", 22.3, 31.8, 2.70, 58.0, 315.0, 185.0, 0.95),
    ("146455121", 56.9, 29.7, 3.10, 67.3, 634.0, 431.0, 2.76),
    ("146649042", 22.8, 13.4, 1.70, 56.0, 343.0, 259.0, 2.06),
]

def main():
    print(f"{'strategy':>10} {'ann%':>7} {'dd%':>6} {'calmar_pg':>9} {'calmar_calc':>11} {'ratio':>6} "
          f"{'pf_pg':>6} {'pf_calc':>7} {'diff%':>6}")
    for sid, ann, dd, pf_page, win, aw, al, cal_page in ROWS:
        cal_calc = ann / dd
        w = win / 100.0
        pf_calc = (w * aw) / ((1 - w) * al)
        print(f"{sid:>10} {ann:>7.1f} {dd:>6.1f} {cal_page:>9.2f} {cal_calc:>11.2f} "
              f"{cal_page/cal_calc:>6.2f} {pf_page:>6.2f} {pf_calc:>7.2f} "
              f"{(pf_page/pf_calc-1)*100:>+6.1f}")

if __name__ == "__main__":
    main()

