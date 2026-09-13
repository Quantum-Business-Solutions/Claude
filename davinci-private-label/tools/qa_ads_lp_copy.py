#!/usr/bin/env python3
"""QA the ad landing-page copy against every standing client rule.

Rules checked (source in brackets):
  R1  no "custom formulation"                                   [Sarah, 24 Aug]
  R2  FoodScience LLC, never FoodScience Corp/Corporation       [Sarah, 24 Aug]
  R3  no "DaVinci" anywhere, no link to a DaVinci property      [Sarah / Tammy]
  R4  Provider language: no first-person manufacturing claim    [Sarah / Mindy]
      allowed: "US manufacturing", "turnkey production",
               "manufactured in a US facility", "cGMP facility"
      banned:  "we manufacture", "we produce", "our facility",
               "our facilities", "our manufacturing", "our plant",
               "Praxera Laboratories", "we are a manufacturer"
  R5  no purchase path / e-commerce wording                     [Tammy, 8 Sep]
  R6  CTAs point at /get-started                                [Tammy, 8 Sep]
  R7  no "Praxera Laboratories" / "Praxera Labs"                [Shawn, 13 Sep]
  R8  catalogue size stated as 190-plus, never 250              [/about, live]
  R9  no leftover [PLACEHOLDER ...] text                        [this task]
  R10 Daily Best always carries (R)                             [Tammy, 8 Sep]
"""
import json
import re
import sys

sys.argv = [sys.argv[0]]          # keep the builder in dry-run
import importlib.util
spec = importlib.util.spec_from_file_location('b', 'tools/build_ads_lp_copy.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def plain(html):
    txt = re.sub(r'<[^>]+>', ' ', html)
    txt = txt.replace('&mdash;', '-').replace('&nbsp;', ' ').replace('&amp;', '&')
    return re.sub(r'\s+', ' ', txt).strip()


BANNED = [
    (r'custom formulation', 'R1  banned phrase "custom formulation"'),
    (r'FoodScience Corp', 'R2  must be FoodScience LLC'),
    (r'da\s?vinci', 'R3  DaVinci reference'),
    (r'\bwe manufacture\b', 'R4  first-person manufacturing claim'),
    (r'\bwe produce\b', 'R4  first-person production claim'),
    (r'\bour facilit(y|ies)\b', 'R4  "our facility/facilities"'),
    (r'\bour manufacturing\b', 'R4  "our manufacturing"'),
    (r'\bour plant\b', 'R4  "our plant"'),
    (r'\bwe are a (contract )?manufacturer\b', 'R4  Praxera described as a manufacturer'),
    (r'\bour (production )?(site|sites)\b', 'R4  first-person site ownership'),
    (r'\badd to (cart|basket)\b', 'R5  purchase path'),
    (r'\bbuy now\b', 'R5  purchase path'),
    (r'\bshop now\b', 'R5  purchase path'),
    (r'\bcheckout\b', 'R5  purchase path'),
    (r'praxera (laboratories|labs)', 'R7  "Praxera Laboratories" is not a thing'),
    (r'\b250[- ]?(plus|\+)? ?products?\b', 'R8  catalogue is 190-plus, not 250'),
    (r'\[PLACEHOLDER', 'R9  placeholder text left in copy'),
    (r'Daily Best(?!\s*&reg;|\s*®)', 'R10 Daily Best without the (R)'),
]

ALLOWED_MFG = [
    'us manufacturing', 'turnkey production',
    'manufactured in a us facility', 'manufactured in an fda-registered',
    'manufactured in a vermont facility',
    'dietary supplement manufacturing', 'cgmp facility',
    'supplement contract manufacturer',   # the searcher's term, in a question
    'contract manufacturing or private label',
    'contract manufacturing usually means',
    'private label and contract manufacturing',   # the searcher's own question
    'why does us manufacturing matter',
    'is us manufacturing more expensive',
]

problems = []
report = {}

for slug in b.BODY:
    fields = {
        'hero.headline': b.HERO[slug]['headline'],
        'hero.subhead': b.HERO[slug]['subhead'],
        'body': b.BODY[slug],
        'metaDescription': b.META[slug],
    }
    for i, c in enumerate(b.CARDS):
        fields[f'card{i}.title'] = c['title']
        fields[f'card{i}.body'] = c['content']
    for i, s in enumerate(b.STATS):
        fields[f'stat{i}'] = f"{s['value']} {s['stat_label']}"
    for i, (q, a) in enumerate(b.FAQ[slug]):
        fields[f'faq{i}.q'] = q
        fields[f'faq{i}.a'] = a

    for name, raw in fields.items():
        txt = plain(raw)
        low = txt.lower()
        for pat, why in BANNED:
            for m in re.finditer(pat, low, re.I):
                problems.append((slug, name, why, txt[max(0, m.start() - 60):m.end() + 60]))
        # every mention of manufactur* must sit inside an approved construction
        for m in re.finditer(r'manufactur\w*', low):
            window = low[max(0, m.start() - 45):m.end() + 45]
            if not any(a in window for a in ALLOWED_MFG):
                problems.append((slug, name, 'R4  unapproved manufactur* usage',
                                 txt[max(0, m.start() - 60):m.end() + 60]))
    report[slug] = fields

# R6 - CTA destinations
if b.CTA_HREF != '/get-started':
    problems.append(('*', 'CTA', 'R6  CTA must point at /get-started', b.CTA_HREF))

# R3 - no outbound link to a DaVinci / FoodScience property
for slug, fields in report.items():
    for name, raw in fields.items():
        for href in re.findall(r'href="([^"]+)"', raw):
            if re.search(r'davinci|foodscience|fsc-live|pettech', href, re.I):
                problems.append((slug, name, 'R3  link to a non-Praxera property', href))

print(f'checked {sum(len(f) for f in report.values())} copy fields '
      f'across {len(report)} pages\n')
if problems:
    for slug, name, why, ctx in problems:
        print(f'FAIL  {slug:22} {name:18} {why}\n      ...{ctx}...')
    print(f'\n{len(problems)} problem(s)')
    sys.exit(1)
print('PASS - no rule violations in the new copy.')
