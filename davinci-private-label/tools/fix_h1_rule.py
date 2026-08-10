#!/usr/bin/env python3
"""Make the visual gate and the promotion harness agree with the copy gate about <h1>.

privacy and terms measure zero visible differences at 1440, 768 and 390 with
identical copy, and still fail -- because gate.py and promote.py demand exactly
one <h1> while V1 gives those two pages none. check.py already encodes the right
rule and says so in its own docstring: adding a heading V1 does not have would be
a change, not a fix. Three gates in one project should not disagree.

Staged rather than applied: the promotion run imports gate.py on every page, so
editing it mid-run would measure later pages against a different instrument than
earlier ones. Run this once the queue is clear, then re-gate privacy and terms.

usage: fix_h1_rule.py --check | --apply
"""
import os, re, sys

S = os.path.dirname(os.path.abspath(__file__)) + '/'

GATE_OLD = """    n_h1 = len(re.findall(r'<h1[\\s>]', hl))
    if n_h1 != 1: fails.append(f"{n_h1} <h1> elements, expected 1")"""

GATE_NEW = """    # Match V1's heading structure rather than an absolute rule. privacy and
    # terms have no <h1> at all, so requiring one would mean inventing a heading
    # the original never had. Where V1 has more than one -- aging authored its
    # FAQ heading as a second <h1> -- collapsing to one is the deliberate fix.
    n_h1 = len(re.findall(r'<h1[\\s>]', hl))
    want_h1 = 1 if len(re.findall(r'<h1[\\s>]', hr)) >= 1 else 0
    if n_h1 != want_h1:
        fails.append(f"{n_h1} <h1> elements, expected {want_h1} to match V1")"""


def patch(path, old, new, label):
    s = open(path).read()
    if new.strip().splitlines()[-1] in s:
        print(f"  already applied  {label}"); return True
    if old not in s:
        print(f"  NOT FOUND in {label} -- the file has moved on; patch by hand"); return False
    open(path, 'w').write(s.replace(old, new, 1))
    print(f"  patched  {label}")
    return True


if __name__ == '__main__':
    if '--apply' not in sys.argv:
        s = open(S + 'vis/gate.py').read()
        print("  gate.py currently demands one <h1>:", GATE_OLD.strip().splitlines()[-1] in s)
        print("  run with --apply once no promotion or gate run is in flight")
        sys.exit(0)
    ok = patch(S + 'vis/gate.py', GATE_OLD, GATE_NEW, 'vis/gate.py')
    print("\nNow re-gate privacy (216194811650 / 219006293567) and "
          "terms (216194811759 / 219004967737), then promote them.")
    sys.exit(0 if ok else 1)
