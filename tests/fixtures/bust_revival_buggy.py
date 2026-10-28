def run(returns, lev=5.0):
    cap = 1.0
    for r in returns:
        cap *= 1 + lev * r
        if cap <= 0:
            cap = 0.01          # revived at 1% and keeps compounding
    return cap

def run_clamp(returns, lev=5.0):
    cap = 1.0
    for r in returns:
        cap = max(cap * (1 + lev * r), 0.01)
    return cap
