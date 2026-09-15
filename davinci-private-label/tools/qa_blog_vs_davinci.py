#!/usr/bin/env python3
"""QA every Praxera blog post against the DaVinci post it was migrated from.

Both blogs live in portal 4087538, so the originals are read straight from the
API rather than scraped: DaVinci "Private Label Supplements Blog" is content
group 20252938412, Praxera is 220598739286. Slugs line up as
`private-label/<x>` -> `blog/<x>`.

Read-only on both sides. DaVinci content is never written to.

Reports, per post:
  * body length against the original, so a truncated migration is obvious
  * headings present in the original and missing from Praxera, with their level
  * headings whose level changed
  * links still pointing at davincilabs.com or blog.davincilabs.com
  * "DaVinci" / "FoodScience" left in the copy
  * "custom formulation" - banned site-wide (Sarah)
  * lower-case h2/h3, counted on BOTH sides so an inherited fault is not
    mistaken for something the migration did

usage: python3 tools/qa_blog_vs_davinci.py
       python3 tools/qa_blog_vs_davinci.py --md deliverables/BLOG_QA.md
"""
import argparse
import json
import re

exec(open('/tmp/hs.py').read())  # noqa: provides call()

DAVINCI_BLOG = '20252938412'
PRAXERA_BLOG = '220598739286'


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


def body_of(post):
    w = post.get('widgets') or {}
    inner = ((w.get('article_body') or {}).get('body') or {}).get('content')
    return inner or post.get('postBody') or ''


def headings(html):
    return [(m.group(1).lower(), re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(2))).strip())
            for m in re.finditer(r'<(h[1-4])[^>]*>(.*?)</\1>', html, re.S | re.I)]


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def lower_headings(hs):
    """Headings that start lower-case - a heading should not."""
    return [t for lvl, t in hs if lvl in ('h2', 'h3') and t[:1].islower()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md')
    a = ap.parse_args()

    dv = {p['slug'].split('/', 1)[-1]: p for p in
          paged('/cms/v3/blogs/posts', 'id,name,slug,archivedInDashboard',
                contentGroupId=DAVINCI_BLOG) if not p.get('archivedInDashboard')}
    px = {p['slug'].split('/', 1)[-1]: p for p in
          paged('/cms/v3/blogs/posts', 'id,name,slug,url,currentState,archivedInDashboard',
                contentGroupId=PRAXERA_BLOG) if not p.get('archivedInDashboard')}
    print(f'DaVinci originals: {len(dv)}   Praxera posts: {len(px)}')

    rows, unmatched = [], []
    for key, p in sorted(px.items()):
        if key not in dv:
            unmatched.append((key, p.get('name', '')))
            continue
        pb = body_of(call('GET', f"/cms/v3/blogs/posts/{p['id']}"))
        db = body_of(call('GET', f"/cms/v3/blogs/posts/{dv[key]['id']}"))
        ph, dh = headings(pb), headings(db)
        pset = {norm(t) for _, t in ph}
        missing = [(lvl, t) for lvl, t in dh if norm(t) and norm(t) not in pset]
        plevel = {norm(t): lvl for lvl, t in ph}
        moved = [(t, lvl, plevel[norm(t)]) for lvl, t in dh
                 if norm(t) in plevel and plevel[norm(t)] != lvl]
        rows.append({
            'key': key, 'name': p.get('name', ''), 'url': p.get('url', ''),
            'state': p.get('currentState'),
            'px_chars': len(pb), 'dv_chars': len(db),
            'px_heads': len(ph), 'dv_heads': len(dh),
            'missing': missing, 'moved': moved,
            'davinci_links': sorted(set(re.findall(r'https?://[^"\')\s]*davincilabs\.com[^"\')\s]*', pb))),
            'brand_words': sorted({w for w in re.findall(r'DaVinci|FoodScience', pb, re.I)}),
            'custom_formulation': len(re.findall(r'custom formulation', pb, re.I)),
            'px_lower': lower_headings(ph), 'dv_lower': lower_headings(dh),
        })

    short = [r for r in rows if r['dv_chars'] and r['px_chars'] < r['dv_chars'] * 0.9]
    miss = [r for r in rows if r['missing']]
    dvl = [r for r in rows if r['davinci_links']]
    bw = [r for r in rows if r['brand_words']]
    cf = [r for r in rows if r['custom_formulation']]
    low = [r for r in rows if r['px_lower']]
    inherited = [r for r in low if r['dv_lower']]

    print(f'\nmatched pairs                        : {len(rows)}')
    print(f'no DaVinci counterpart               : {len(unmatched)}')
    print(f'body >10% shorter than the original  : {len(short)}')
    print(f'headings missing vs the original     : {len(miss)}')
    print(f'links still pointing at davincilabs  : {len(dvl)}')
    print(f'"DaVinci"/"FoodScience" left in copy  : {len(bw)}')
    print(f'"custom formulation" (banned)        : {len(cf)}')
    print(f'lower-case headings                  : {len(low)}  '
          f'(of which already lower-case on DaVinci: {len(inherited)})')

    json.dump({'rows': rows, 'unmatched': unmatched}, open('/tmp/blog_qa.json', 'w'), indent=1)
    print('\ndetail -> /tmp/blog_qa.json')

    if a.md:
        with open(a.md, 'w') as f:
            f.write(render(rows, unmatched, short, miss, dvl, bw, cf, low, inherited))
        print('report ->', a.md)


def render(rows, unmatched, short, miss, dvl, bw, cf, low, inherited):
    o = []
    w = o.append
    w('# Praxera blog QA against the DaVinci originals\n')
    w('Every Praxera post compared with the DaVinci post it was migrated from. Both blogs are in '
      'portal 4087538, so the originals are read from the API, not scraped. Read-only on both '
      'sides — no DaVinci content was written to.\n')
    w('| Check | Posts |')
    w('|---|---|')
    w(f'| Matched pairs | {len(rows)} |')
    w(f'| No DaVinci counterpart | {len(unmatched)} |')
    w(f'| **Body more than 10% shorter than the original** | **{len(short)}** |')
    w(f'| **Headings missing vs the original** | **{len(miss)}** |')
    w(f'| Links still pointing at davincilabs.com | {len(dvl)} |')
    w(f'| "DaVinci" or "FoodScience" left in the copy | {len(bw)} |')
    w(f'| "custom formulation" — banned site-wide | {len(cf)} |')
    w(f'| Lower-case headings | {len(low)} — {len(inherited)} of them already lower-case on DaVinci |')
    w('')

    if short:
        w('## Shorter than the original\n')
        w('Body character count, Praxera against DaVinci. A big drop means content did not '
          'come across.\n')
        w('| Post | Praxera | DaVinci | Lost | Headings |')
        w('|---|---:|---:|---:|---|')
        for r in sorted(short, key=lambda x: x['px_chars'] / max(x['dv_chars'], 1)):
            pct = 100 - round(100 * r['px_chars'] / r['dv_chars'])
            w(f"| [{r['name'][:58]}]({r['url']}) | {r['px_chars']:,} | {r['dv_chars']:,} | "
              f"**{pct}%** | {r['px_heads']} of {r['dv_heads']} |")
        w('')

    if miss:
        w('## Headings that did not come across\n')
        for r in sorted(miss, key=lambda x: -len(x['missing'])):
            w(f"**[{r['name'][:70]}]({r['url']})** — {len(r['missing'])} missing\n")
            for lvl, t in r['missing'][:14]:
                w(f'- `{lvl}` {t[:100]}')
            if len(r['missing']) > 14:
                w(f'- …and {len(r["missing"]) - 14} more')
            w('')

    if dvl or bw or cf:
        w('## Leftovers from DaVinci\n')
        for r in rows:
            bits = []
            if r['davinci_links']:
                bits.append('links: ' + ', '.join(r['davinci_links'][:3]))
            if r['brand_words']:
                bits.append('words: ' + ', '.join(r['brand_words']))
            if r['custom_formulation']:
                bits.append(f'"custom formulation" ×{r["custom_formulation"]}')
            if bits:
                w(f"- **{r['name'][:64]}** — " + '; '.join(bits))
        w('')

    if low:
        w('## Lower-case headings\n')
        w(f'{len(low)} posts have an h2 or h3 that starts lower-case. **{len(inherited)} of them '
          'are lower-case on the DaVinci original too** — the fault came across with the '
          'migration rather than being introduced by it. Worth fixing on Praxera either way.\n')
        w('| Post | Lower-case headings | Also lower-case on DaVinci |')
        w('|---|---:|---|')
        for r in sorted(low, key=lambda x: -len(x['px_lower'])):
            w(f"| [{r['name'][:56]}]({r['url']}) | {len(r['px_lower'])} | "
              f"{'yes' if r['dv_lower'] else '**no — introduced here**'} |")
        w('')

    if unmatched:
        w('## Praxera posts with no DaVinci counterpart\n')
        w('New writing, or the slug changed. Nothing to compare against.\n')
        for k, n in unmatched:
            w(f'- {n[:80]}  `{k}`')
        w('')
    return '\n'.join(o) + '\n'


if __name__ == '__main__':
    main()
