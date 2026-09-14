#!/usr/bin/env python3
"""Push the seven pages Shawn approved on 14 Sep from draft to live.

Excludes `request-quote` (an unpublished draft - publishing it would put a page
live that was deliberately held back) and the 18 category pages, which carry
another team's in-progress #consultation-form anchor work in their drafts.

Re-reads and gates every page before publishing: the JSON-LD must parse, must be
free of first-person production claims, and must not have gained anyone else's
draft work since 13 Sep. Refuses to publish anything that fails.

Rollback point: backups/pre-publish-2026-09-14/*.live-before-publish.json holds
each page exactly as it was live before this ran.

usage: publish_approved_7.py            # gate only, publishes nothing
       publish_approved_7.py --apply    # gate, then push all seven live
"""
import json
import re
import sys

exec(open('/tmp/hs.py').read())

PAGES = {
    '216189433405': '(home)',
    '221518507280': 'health-categories',
    '216186379328': 'quality-standards',
    '216192983650': 'contact',
    '216192983652': 'alp/ads-mfg-usa',
    '216192983654': 'alp/ads-contract-mfg',
    '216194811734': 'alp/ads-pl-mfg',
}

BAD = re.compile(r'(we produce\b|our facilit(y|ies)\b|produced by a manufacturer \(us\)'
                 r'|produced in our [^"]*facility|manufacturing-side compliance)', re.I)


def gate(pid, label):
    draft = call('GET', f'/cms/v3/pages/site-pages/{pid}/draft')
    head = draft.get('headHtml') or ''
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', head, re.S)
    problems = []
    for b in blocks:
        try:
            json.loads(b)
        except Exception as e:
            problems.append(f'ld+json does not parse: {e}')
        hit = BAD.search(b)
        if hit:
            problems.append(f'banned claim still in schema: {hit.group(0)}')
    fn = label.replace('/', '_').replace('(', '').replace(')', '')
    try:
        prev = json.load(open(
            f'backups/schema-language/{fn}.draft.2026-09-13.json'))['headHtml'] or ''
    except FileNotFoundError:
        prev = head
    if 'ANCHOR' in head and 'ANCHOR' not in prev:
        problems.append("draft gained another team's anchor work since 13 Sep")
    return problems


def main():
    blocked = False
    for pid, label in PAGES.items():
        problems = gate(pid, label)
        if problems:
            blocked = True
            print(f'{label:24} REFUSED')
            for p in problems:
                print(f'    {p}')
        else:
            print(f'{label:24} ready')
    if blocked:
        raise SystemExit('\nnothing published - fix the above first')
    if '--apply' not in sys.argv:
        print('\nGATE ONLY - pass --apply to push all seven live.')
        return
    for pid, label in PAGES.items():
        call('POST', f'/cms/v3/pages/site-pages/{pid}/draft/push-live', b={})
        print(f'{label:24} pushed live')


if __name__ == '__main__':
    main()
