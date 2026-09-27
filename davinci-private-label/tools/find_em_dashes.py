#!/usr/bin/env python3
"""Count em-dashes ("—", U+2014) in every published Praxera blog post.

The em-dash is the classic AI-writing tell Shawn wants purged from the
migrated copy. This scans each post's live article_body, hero subhead and
faq answers (the reader-facing widget fields), and reports every hit with
enough surrounding text to find it fast in the editor.

Excludes the DaVinci blog (content group 20252938412) — read-only there
anyway per standing rules, and the ask is about the Praxera copy.

Read-only. Nothing is written.

usage: python3 tools/find_em_dashes.py
       python3 tools/find_em_dashes.py --md deliverables/EM_DASH_SWEEP.md
"""
import argparse
import re

exec(open('/tmp/hs.py').read())  # noqa: provides call()

PRAXERA_BLOG = '220598739286'
DASH = '—'


def paged(endpoint, props=None, **extra):
    after = None
    while True:
        q = {'limit': 100}
        q.update(extra)
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


def strip_tags(s):
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s or '', flags=re.S)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)).strip()


def widget_texts(post):
    """(field label, plain text) for the reader-facing widget fields."""
    w = post.get('widgets') or {}
    out = []
    body = ((w.get('article_body') or {}).get('body') or {}).get('content')
    if body:
        out.append(('article_body', strip_tags(body)))
    hero = (w.get('hero') or {}).get('body') or {}
    for f in ('subhead', 'headline', 'eyebrow'):
        if hero.get(f):
            out.append((f'hero.{f}', strip_tags(hero[f])))
    faq = (w.get('faq') or {}).get('body') or {}
    for i, item in enumerate(faq.get('faq_items') or faq.get('items') or []):
        if isinstance(item, dict):
            for f in ('question', 'answer'):
                if item.get(f):
                    out.append((f'faq[{i}].{f}', strip_tags(item[f])))
    disc = (w.get('disclaimer') or {}).get('body') or {}
    if disc.get('text') or disc.get('html'):
        out.append(('disclaimer', strip_tags(disc.get('text') or disc.get('html'))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md')
    a = ap.parse_args()

    posts = [p for p in paged('/cms/v3/blogs/posts', 'id,name,slug,url,currentState',
                              contentGroupId=PRAXERA_BLOG)
             if not p.get('archivedInDashboard') and p.get('currentState') == 'PUBLISHED']
    print(f'published Praxera posts: {len(posts)}')

    rows = []
    total = 0
    for p in sorted(posts, key=lambda x: x.get('name', '')):
        full = call('GET', f"/cms/v3/blogs/posts/{p['id']}")
        hits = []
        for field, text in widget_texts(full):
            for m in re.finditer(DASH, text):
                total += 1
                hits.append({
                    'field': field,
                    'context': text[max(0, m.start() - 60):m.start() + 40].strip(),
                })
        if hits:
            rows.append({'name': p.get('name', ''), 'url': p.get('url', ''),
                        'id': p['id'], 'hits': hits})

    print(f'\nposts with at least one em-dash : {len(rows)}')
    print(f'total em-dash occurrences        : {total}')
    print()
    for r in sorted(rows, key=lambda x: -len(x['hits'])):
        print(f"{len(r['hits']):>3}  {r['name'][:64]}  ({r['url']})")

    if a.md:
        with open(a.md, 'w') as f:
            f.write(render(rows, len(posts), total))
        print('\nreport ->', a.md)


def render(rows, n_posts, total):
    o = []
    w = o.append
    w('# Em-dash sweep — Praxera blog\n')
    w(f'Scanned all {n_posts} published Praxera blog posts (article body, hero subhead/headline/'
      'eyebrow, FAQ Q&A, disclaimer). Looking for the em-dash character ("—", U+2014), a common '
      'AI-writing tell.\n')
    w(f'**{total} occurrences across {len(rows)} posts.**\n')
    if not rows:
        w('None found.\n')
        return '\n'.join(o) + '\n'
    w('| Post | Count | Field(s) |')
    w('|---|---:|---|')
    for r in sorted(rows, key=lambda x: -len(x['hits'])):
        fields = ', '.join(sorted({h['field'] for h in r['hits']}))
        w(f"| [{r['name'][:60]}]({r['url']}) | {len(r['hits'])} | {fields} |")
    w('')
    w('## Every occurrence, with context\n')
    for r in sorted(rows, key=lambda x: -len(x['hits'])):
        w(f"### {r['name']}")
        w(f"{r['url']}\n")
        for h in r['hits']:
            w(f"- `{h['field']}` — …{h['context']}…")
        w('')
    return '\n'.join(o) + '\n'


if __name__ == '__main__':
    main()
