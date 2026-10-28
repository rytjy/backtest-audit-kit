def run(returns, lev=5.0):
    cap = 1.0
    for r in returns:
        cap *= 1 + lev * r
        if cap <= 0:
            return 0.0          # account is gone; stop
    return cap

def ratio(a, b):
    return a / max(b, 1e-9)     # division guard, not a revival
