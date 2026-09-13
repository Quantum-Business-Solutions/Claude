"""Apply the approved Tier 1 / Tier 2 'manufacturer' -> Provider language rewrites.

Usage:  python3 apply_manufacturer_language.py [dry|apply]
Reads the plan from manufacturer_language_plan.json. Credentials come from /tmp/hs.py
(supplied by the user in chat) -- never stored in this repo.
"""
import json, sys, os
exec(open('/tmp/hs.py').read())

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'manufacturer_language_plan.json')))
MODE = sys.argv[1] if len(sys.argv) > 1 else 'dry'

def get_path(kind, i):
    return {'email': '/marketing/v3/emails/' + i,
            'page': '/cms/v3/pages/site-pages/' + i,
            'post': '/cms/v3/blogs/posts/' + i}[kind]

def repl(o, old, new, counter):
    if isinstance(o, str):
        n = o.count(old)
        if n:
            counter[0] += n
            return o.replace(old, new)
        return o
    if isinstance(o, dict):
        return {k: repl(v, old, new, counter) for k, v in o.items()}
    if isinstance(o, list):
        return [repl(v, old, new, counter) for v in o]
    return o

def count(o, s):
    if isinstance(o, str): return o.count(s)
    if isinstance(o, dict): return sum(count(v, s) for v in o.values())
    if isinstance(o, list): return sum(count(v, s) for v in o)
    return 0

ok = True
for a in PLAN:
    kind, i = a['kind'], a['id']
    live = call('GET', get_path(kind, i))                 # re-read immediately before writing
    if kind == 'email':
        field = 'content'
    elif kind == 'post':
        field = 'widgets'
    else:
        field = 'widgetContainers' if live.get('widgetContainers') else 'layoutSections'
    obj = live[field]
    for e in a['edits']:
        c = [0]
        obj = repl(obj, e['old'], e['new'], c)
        status = 'OK' if c[0] == 1 else 'PROBLEM(%d)' % c[0]
        if c[0] != 1: ok = False
        print('%-5s %-14s %-12s hits=%s  %s' % (kind, i, status, c[0], e['old'][:70]))
    if MODE == 'apply' and ok:
        call('PATCH', get_path(kind, i), b={field: obj})
        after = call('GET', get_path(kind, i))
        for e in a['edits']:
            old_left = count(after[field], e['old'])
            new_found = count(after[field], e['new'])
            print('   verify %s: old_remaining=%d new_present=%d %s' % (
                i, old_left, new_found, 'OK' if old_left == 0 and new_found >= 1 else 'FAIL'))
print('ALL MATCHES UNIQUE' if ok else 'MISMATCHES -- NOTHING SHOULD BE WRITTEN')
