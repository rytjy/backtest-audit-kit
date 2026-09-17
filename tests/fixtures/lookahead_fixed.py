"""Fixture: the same generator, fixed (case 1, correct side).

The exit is evaluated only on the CURRENT bar as the backtest advances, so no
decision on bar ``i`` can see bar ``i+1``. This file must produce ZERO findings
from ``auditkit.checks.lookahead``.
"""


def generate_signals(df, TO=24, SL=0.01, TP=0.02):
    n = len(df)
    entries = []
    open_trade = None
    for i in range(n):
        if open_trade is None:
            if condition(df, i):
                open_trade = i
                entries.append((i, None))
        else:
            # Exit checked against the CURRENT bar only.
            px = df["close"].iloc[i]
            if px <= stop_price(df, open_trade, SL):
                entries[-1] = (open_trade, "SL")
                open_trade = None
            elif px >= target_price(df, open_trade, TP):
                entries[-1] = (open_trade, "TP")
                open_trade = None
    return entries


def momentum(df):
    # Positive lag = reads the past. Clean.
    return df["close"] - df["close"].shift(1)


def trailing_mean(df, i, lb=24):
    # Window ends at the CURRENT bar: lower bound is `i - lb`, never `i + k`.
    lo = max(0, i - lb)
    return df["close"].iloc[lo : i + 1].mean()


# --- stubs --------------------------------------------------------------- #
def condition(df, i):
    return True


def stop_price(df, ei, sl):
    return df["close"].iloc[ei] * (1 - sl)


def target_price(df, ei, tp):
    return df["close"].iloc[ei] * (1 + tp)
