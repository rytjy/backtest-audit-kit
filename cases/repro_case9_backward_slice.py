"""Reproduce Case 9: a backward rolling window is reported as a future slice.

Run from the repository root:
    python3 cases/repro_case9_backward_slice.py

Expected: the in-loop backward window is HIGH/FUTURE_SLICE, the same window
without "+1" is clean, and a genuine forward read is reported.
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

BACKWARD_NO_PLUS_ONE = '''
def rolling(c, n):
    out = []
    for i in range(n, len(c)):
        w = c[i-n:i]              # ends at i-1
        out.append(sum(w)/len(w))
    return out
'''

FORWARD_READ = '''
def peek(c, i):
    for j in range(len(c)):
        x = c[j+1]
    return x
'''


def show(name, source):
    findings = detect(source, name + ".py")
    print(name)
    for f in findings:
        print("   [%s] %s L%d  %s" % (f.severity, f.rule, f.lineno, f.message))
    if not findings:
        print("   (no findings)")
    return findings


def main():
    backward = show("backward_loop", BACKWARD_LOOP)
    clean = show("backward_without_plus_one", BACKWARD_NO_PLUS_ONE)
    forward = show("forward_read", FORWARD_READ)

    flagged = [(f.rule, f.severity) for f in backward]
    print()
    print("backward window flagged HIGH:", ("FUTURE_SLICE", "HIGH") in flagged)
    print("same window without +1 clean:", len(clean) == 0)
    print("forward read still reported:", len(forward) > 0)


if __name__ == "__main__":
    main()
