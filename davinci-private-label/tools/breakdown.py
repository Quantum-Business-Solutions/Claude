#!/usr/bin/env python3
"""Split the geometry differences into ones a visitor can see and ones they can't.

A width-only difference on an element whose text and position are identical is a
measurement artifact, not a regression: V1 sizes the FAQ <summary> span to its
text inside a flex row, the module gives the same span the full row width. Same
glyphs, same place, wider invisible box. A font-size, weight or colour difference
is real -- that changes pixels.

usage: breakdown.py [page-name ...]
"""
import os, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify import visit, V1SEL, V3SEL
from shot import mirror

S = os.path.dirname(os.path.abspath(__file__)) + '/'


def classify(A, B):
    """Compare elements matched by their text.

    Keyed by a plain dict, repeated text collapsed to whichever element came
    last: capsules alone has six repeated labels, and one of the discarded
    pairs carried a real colour difference. Elements are grouped by text and
    compared in document order within each group, so nothing is silently
    dropped."""
    from collections import defaultdict
    GA, GB = defaultdict(list), defaultdict(list)
    for e in A['el']: GA[e['t']].append(e)
    for e in B['el']: GB[e['t']].append(e)
    real, artifact = [], []
    for t, group in GA.items():
        for a, b in zip(group, GB.get(t, [])):
            keys = ('fs', 'fw', 'color') if a.get('own', True) else ()
            visible = [k for k in keys if a[k] != b[k]]
            wider = abs(a['w'] - b['w']) > 6
            # A box that is wider but the same height holds the same glyphs in
            # the same place -- V1 shrink-wraps a flex child, the module gives it
            # the full row. A box that is wider AND a different height has
            # re-wrapped its text, which a reader sees, so it is not an artifact.
            rewrapped = wider and abs(a.get('h', 0) - b.get('h', 0)) > 4
            if visible or rewrapped:
                if rewrapped: visible = visible + ['measure']
                real.append((t, {k: (a[k], b[k]) for k in visible if k != 'measure'}
                                | ({'measure': (a['w'], b['w']),
                                    'height': (a.get('h'), b.get('h'))} if rewrapped else {}),
                             (a['w'], b['w']) if wider else None))
            elif wider:
                artifact.append((t, a['w'], b['w']))
    return real, artifact


if __name__ == '__main__':
    pm  = json.load(open(S + 'pagemap.json'))
    ids = json.load(open(S + '../fam16/v3_ids.json'))
    out = {}
    for name in (sys.argv[1:] or list(pm)):
        v1id = pm[name]; v3id = ids[v1id]
        d1, d3 = f"{S}mirror/{name}_v1", f"{S}mirror/{name}_v3"
        # V1 is only ever mirrored once -- the promoted record no longer holds the
        # original markup, so these captures are the sole record of how V1 looked.
        if not os.path.exists(d1 + '/index.html'): mirror(v1id, d1)
        # V3 is always re-mirrored. A cached V3 silently reports the state of an
        # older build, which is exactly how four pages were once judged broken.
        shutil.rmtree(d3, ignore_errors=True)
        mirror(v3id, d3)
        real, art = classify(visit(d1, V1SEL), visit(d3, V3SEL))
        out[name] = {'real': real, 'artifact': art}
        print(f"  {name:20} real {len(real):3}   width-only {len(art):3}")
        for t, d, w in real:
            print(f"       REAL  {t[:56]!r}  {d}" + (f"  w{w}" if w else ""))
    json.dump(out, open(S + 'breakdown.json', 'w'), indent=1)
