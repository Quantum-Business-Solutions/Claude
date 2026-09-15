#!/usr/bin/env python3
"""Look for "1976" anywhere a person could read it.

FoodScience has been in business since 1973 (Shawn, 15 Sep). This sweeps the
portal for a wrong year.

The catch is that a naive search is almost all noise: "1976" falls inside
HubSpot's own ids all over the JSON - module_id 119762877841 contains it, and
there are 182 such matches on the site pages alone. So a hit only counts when
1976 is not part of a longer number, and the search runs over the *text* of a
field rather than the serialised object where ids live. 1973 is reported the
same way for comparison.

Covers: site pages, landing pages, blog posts, marketing emails, forms and the
theme source, each in both its published and draft state where it has one.

Read-only. Nothing is written.

usage: python3 tools/find_year_1976.py
       python3 tools/find_year_1976.py --years 1976,1973,1974
"""
import argparse
import json
import re
import urllib.parse
import urllib.request

exec(open('/tmp/hs.py').read())  # noqa: provides call()

TOKEN = re.search(r'pat-na1-[0-9a-f-]+', open('/tmp/hs.py').read()).group(0)

# ids are digits; a real year is not wedged between other digits
def matches(text, year):
    return list(re.finditer(rf'(?<!\d){year}(?!\d)', text or ''))


# fields that carry copy rather than plumbing
TEXTY = re.compile(r'(html|body|content|text|headline|subhead|eyebrow|label|title|name|'
                   r'description|caption|value|alt|answer|question|placeholder|message)$', re.I)


def texts(node, path=''):
    """Every string in the object that lives in a copy-bearing field."""
    if isinstance(node, str):
        if TEXTY.search(path.rsplit('.', 1)[-1].rstrip('0123456789[]')):
            yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from texts(v, f'{path}.{k}')
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from texts(v, f'{path}[{i}]')


def strip_tags(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s))


def scan(kind, ident, obj, years, out):
    for path, s in texts(obj):
        plain = strip_tags(s)
        for y in years:
            for m in matches(plain, y):
                out.append({
                    'year': y, 'kind': kind, 'ident': ident, 'field': path[:60],
                    'context': plain[max(0, m.start() - 70):m.start() + 40].strip(),
                })


def paged(endpoint, props=None):
    after = None
    while True:
        q = {'limit': 100}
        if props:
            q['property'] = props
        if after:
            q['after'] = after
        r = call('GET', endpoint, q=q)
        for x in r.get('results', []):
            yield x
        after = ((r.get('paging') or {}).get('next') or {}).get('after')
        if not after:
            return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', default='1976,1973')
    a = ap.parse_args()
    years = [y.strip() for y in a.years.split(',') if y.strip()]
    out = []

    for label, ep in (('site page', '/cms/v3/pages/site-pages'),
                      ('landing page', '/cms/v3/pages/landing-pages')):
        ids = [(p['id'], p.get('slug') or p.get('name'))
               for p in paged(ep, 'id,slug,name,archivedInDashboard')
               if not p.get('archivedInDashboard')]
        for pid, slug in ids:
            for env, suffix in (('published', ''), ('draft', '/draft')):
                try:
                    scan(f'{label} ({env})', slug, call('GET', f'{ep}/{pid}{suffix}'), years, out)
                except Exception:
                    pass
        print(f'  {label}s: {len(ids)}')

    posts = [(p['id'], p.get('slug')) for p in paged('/cms/v3/blogs/posts', 'id,slug,archivedInDashboard')
             if not p.get('archivedInDashboard')]
    for pid, slug in posts:
        scan('blog post', slug, call('GET', f'/cms/v3/blogs/posts/{pid}'), years, out)
    print(f'  blog posts: {len(posts)}')

    emails = list(paged('/marketing/v3/emails'))
    for e in emails:
        try:
            scan('email', e.get('name'), call('GET', f"/marketing/v3/emails/{e['id']}"), years, out)
        except Exception:
            scan('email', e.get('name'), e, years, out)
    print(f'  emails: {len(emails)}')

    try:
        forms = list(paged('/marketing/v3/forms'))
        for f in forms:
            scan('form', f.get('name'), f, years, out)
        print(f'  forms: {len(forms)}')
    except Exception as ex:
        print('  forms: could not read -', str(ex)[:60])

    # theme source - the modules and templates behind every page
    files = []

    def walk_theme(path):
        u = 'https://api.hubapi.com/cms/v3/source-code/published/metadata/' + urllib.parse.quote(path)
        try:
            meta = json.loads(urllib.request.urlopen(urllib.request.Request(
                u, headers={'Authorization': 'Bearer ' + TOKEN})).read())
        except Exception:
            return
        for child in meta.get('children') or []:
            sub = f'{path}/{child}'
            if re.search(r'\.(html|css|js|json)$', child):
                files.append(sub)
            elif '.' not in child or child.endswith('.module'):
                walk_theme(sub)

    walk_theme('Private Label')
    for f in files:
        u = 'https://api.hubapi.com/cms/v3/source-code/published/content/' + urllib.parse.quote(f)
        try:
            body = urllib.request.urlopen(urllib.request.Request(
                u, headers={'Authorization': 'Bearer ' + TOKEN})).read().decode('utf8', 'replace')
        except Exception:
            continue
        plain = strip_tags(body)
        for y in years:
            for m in matches(plain, y):
                out.append({'year': y, 'kind': 'theme file', 'ident': f, 'field': '',
                            'context': plain[max(0, m.start() - 70):m.start() + 40].strip()})
    print(f'  theme files: {len(files)}')

    json.dump(out, open('/tmp/year_sweep.json', 'w'), indent=1)
    print()
    for y in years:
        sub = [h for h in out if h['year'] == y]
        print(f'===== {y}: {len(sub)} readable occurrences =====')
        for h in sub:
            print(f"   {h['kind']:<24} {str(h['ident'])[:40]:<42} ...{h['context']}")
        print()


if __name__ == '__main__':
    main()
