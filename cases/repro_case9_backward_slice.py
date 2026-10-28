"""Regression check for Case 9: a backward rolling window is not a future leak.

Before 2026-10-28 the checker reported `c[i-n+1:i+1]` (a window ending at `i`) as
HIGH/FUTURE_SLICE. This script asserts the repaired behaviour and guards the
genuinely forward shapes.

Run from the repository root:
    python3 cases/repro_case9_backward_slice.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auditkit.checks.lookahead import detect  # noqa: E402

BACKWARD_LOOP = '''
def rolling(c, n):
    out = []
    for i in range(n, len(c)):
        w = c[i-n+1:i+1]          # ends at i
        out.append(sum(w)/len(w))
    return out
'''

FORWARD_SLICE_LOOP = '''
def peek(c, n):
    out = []
    for i in range(n, len(c)):
        w = c[i+1:i+5]            # starts after i
        out.append(sum(w))
    return out
'''

NET_POSITIVE_OFFSET = '''
def peek(c, n):
    out = []
    for i in range(n, len(c)):
        w = c[(i-3)+5:]           # == i + 2
        out.append(sum(w))
    return out
'''


def rules(name, source):
    findings = detect(source, name + ".py")
    print("%-22s %s" % (name, [(f.rule, f.severity) for f in findings] or "clean"))
    return findings


def main():
    backward = rules("backward_loop", BACKWARD_LOOP)
    forward = rules("forward_slice_loop", FORWARD_SLICE_LOOP)
    net = rules("net_positive_offset", NET_POSITIVE_OFFSET)

    ok = (
        backward == []
        and [f.rule for f in forward] == ["FUTURE_SLICE"]
        and [f.rule for f in net] == ["FUTURE_SLICE"]
    )
    print()
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
