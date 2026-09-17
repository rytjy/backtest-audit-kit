"""Fixture: a backtest generator that leaks the future (case 1, buggy side).

Desensitised. NOT meant to run -- it exists so the linter has something to
find. Every "BUG:" comment marks a construct ``auditkit.checks.lookahead``
should flag.
"""


def generate_signals(df, TO=24, SL=0.01, TP=0.02):
    n = len(df)
    entries = []
    for ei in range(n):
        if not condition(df, ei):
            continue
        # BUG: the future window is scanned on the entry bar itself, so the
        # signal only fires when the outcome is already known.
        hit = None
        for j in range(ei + 1, min(ei + 1 + TO, n)):
            if low(df, j) <= sl_price(df, ei):
                hit = "SL"
                break
            if high(df, j) >= tp_price(df, ei):
                hit = "TP"
                break
        entries.append((ei, hit))
    return entries


def momentum(df):
    # BUG: negative shift pulls the NEXT bar into the current row.
    return df["close"].shift(-1) - df["close"]


def forward_return(df, ei):
    # BUG: open-ended future slice.
    window = df["close"].iloc[ei + 1 : ei + 25]
    # BUG: direct read of the next bar.
    nxt = df["close"].iloc[ei + 1]
    return window.mean(), nxt


# --- stubs so the fixture parses cleanly -------------------------------- #
def condition(df, i):
    return True


def low(df, j):
    return df["low"].iloc[j]


def high(df, j):
    return df["high"].iloc[j]


def sl_price(df, ei):
    return df["close"].iloc[ei] * 0.99


def tp_price(df, ei):
    return df["close"].iloc[ei] * 1.02
