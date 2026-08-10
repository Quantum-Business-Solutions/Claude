#!/usr/bin/env python3
"""Change the catalogue claim from 250 to 190 across the Private Label pages.

This is a content edit, not a conversion, so it is deliberately narrow: it
rewrites the number only where it is the catalogue count, and it walks the whole
page object so it reaches both shapes -- the original pages still hold their copy
in widget HTML, the converted ones hold it in module parameters.

One occurrence must survive: "Gluconic(R) DMG 250 mg" is a product's dosage. A
blind replace would restate a real product's strength, so any 250 followed by a
unit is left alone, and the run reports how many it skipped so the exclusion can
be seen working rather than assumed.

usage: renumber.py --dry      list every change without writing
       renumber.py --apply
"""
import os, re, sys, json, time, urllib.request

TOK  = os.environ['TOKEN']
API  = "https://api.hubapi.com"
S    = os.path.dirname(os.path.abspath(__file__)) + '/'
REPO = '/home/user/Claude/davinci-private-label/snapshots/renumber-250-to-190/'

# 250 as the catalogue count, never as a measurement: a unit after the number
# means it is a dose, a weight or a size.
CLAIM = re.compile(r'\b250(\+?)(?!\s*(?:mg|mcg|g\b|ml|iu|kg|lb|oz|px|%))')
SKIP  = re.compile(r'\b250\s*(?:mg|mcg|g\b|ml|iu|kg|lb|oz)', re.I)


def req(url, method='GET', data=None, tries=4):
    for n in range(tries):
        try:
            r = urllib.request.Request(url, data=data, method=method, headers={
                "Authorization": "Bearer " + TOK, "Content-Type": "application/json"})
            with urllib.request.urlopen(r, timeout=60) as f:
                return json.loads(f.read() or b'{}')
        except Exception:
            if n == tries - 1: raise
            time.sleep(2 ** n)


def walk(node, hits, skips):
    """Rewrite every string in the object, counting what changed and what was spared."""
    if isinstance(node, str):
        skips[0] += len(SKIP.findall(node))
        new, n = CLAIM.subn(lambda m: '190' + m.group(1), node)
        if n:
            hits.extend(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', node[max(0, m.start()-40):m.end()+45])).strip()
                        for m in CLAIM.finditer(node))
        return new
    if isinstance(node, list):
        return [walk(x, hits, skips) for x in node]
    if isinstance(node, dict):
        return {k: walk(v, hits, skips) for k, v in node.items()}
    return node


def main():
    dry = '--apply' not in sys.argv
    os.makedirs(REPO, exist_ok=True)
    pages = []
    after = None
    while True:
        u = f"{API}/cms/v3/pages/site-pages?limit=100&property=id,slug,name"
        if after: u += "&after=" + after
        d = req(u); pages += d['results']
        after = (d.get('paging') or {}).get('next', {}).get('after')
        if not after: break
    targets = [p for p in pages
               if 'pl-demo' in (p.get('slug') or '') and not p['slug'].endswith('-v1ref')]

    changed = total = spared = 0
    for p in sorted(targets, key=lambda x: x['slug']):
        full = req(f"{API}/cms/v3/pages/site-pages/{p['id']}")
        body = {k: full.get(k) for k in ('widgetContainers', 'layoutSections') if full.get(k)}
        if not body: continue
        hits, skips = [], [0]
        new = walk(body, hits, skips)
        spared += skips[0]
        if not hits: continue
        changed += 1; total += len(hits)
        print(f"\n  {p['slug']}  ({len(hits)} change{'s' if len(hits) != 1 else ''})")
        for h in hits[:3]:
            print(f"       ...{h[:96]}")
        if dry: continue
        json.dump(full, open(REPO + f"{p['id']}.json", 'w'), indent=1)   # before-state
        req(f"{API}/cms/v3/pages/site-pages/{p['id']}", 'PATCH',
            json.dumps(new, separators=(',', ':')).encode())
        back = req(f"{API}/cms/v3/pages/site-pages/{p['id']}")
        left = len(CLAIM.findall(json.dumps({k: back.get(k) for k in body})))
        print(f"       written; {left} catalogue 250s remaining on the page")

    print(f"\n{'WOULD CHANGE' if dry else 'CHANGED'}: {total} occurrence(s) on {changed} page(s)")
    print(f"left alone as a dose or measurement: {spared}")


if __name__ == '__main__':
    sys.exit(main())
