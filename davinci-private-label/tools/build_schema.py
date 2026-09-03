"""Generate schema.org structured data for the Praxera site.

Why this exists
---------------
The 63 Praxera pages carry 241 question-and-answer pairs and not one line of
structured data. A person reads those answers fine; a machine sees undifferentiated
markup. Schema labels them, which is what Google's rich results and the AI answer
engines actually parse. For a brand nobody has heard of yet, Organization markup is
also the first step in existing as an entity at all.

How it stays safe
-----------------
Everything is written into `headHtml`, between markers:

    <!-- QBS-SCHEMA:START --> ... <!-- QBS-SCHEMA:END -->

so a re-run replaces its own block and never touches anything else in that field -
several pages already carry hand-written CSS there. The PATCH sends `headHtml` alone,
so concurrent edits to page copy in `layoutSections` are not disturbed.

Re-run it before cutover. FAQ markup is generated FROM the live copy, so if the copy
changes the markup must be regenerated - schema that disagrees with the visible page
is a guideline violation, not a bonus.

Usage:  python3 build_schema.py --dry-run     (default, writes nothing)
        python3 build_schema.py --apply
"""
import sys, json, re, argparse, html as H
sys.path.insert(0, '/tmp')
from hs import call

SITE = "https://www.praxerasupplements.com"
LOGO = "https://www.pettechlabs.com/hubfs/Praxera/Praxera%20Logo.png"
START, END = "<!-- QBS-SCHEMA:START -->", "<!-- QBS-SCHEMA:END -->"

# Pages that must never carry markup:
#   dropshipping    - the client has withdrawn the service; do not help it rank
#   pl-module-*     - internal build references, never published
#   -temporary-slug - duplicate page awaiting deletion
EXCLUDE_EXACT = {"dropshipping", "pl-module-library", "pl-global-blocks"}
EXCLUDE_PREFIX = ("-temporary-slug",)

# Deferred, not excluded. Their Q&A still contains a first-person manufacturing claim
# that Sarah has ruled against. Marking it up would hand that exact claim to Google and
# the answer engines in machine-readable form - the opposite of what she asked for.
# Remove from this set and re-run once her rewrite has landed.
DEFER = {"certifications", "chewables"}


def excluded(slug):
    return slug in EXCLUDE_EXACT or slug in DEFER or slug.startswith(EXCLUDE_PREFIX)


def plain(s):
    """HTML fragment -> the sentence a visitor actually reads."""
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'</p>\s*<p[^>]*>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = H.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def collect_qa(obj, out):
    if isinstance(obj, dict):
        q, a = obj.get('question'), obj.get('answer')
        if isinstance(q, str) and isinstance(a, str):
            q, a = plain(q), plain(a)
            if len(q) > 5 and len(a) > 15:
                out.append((q, a))
        for v in obj.values():
            collect_qa(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_qa(v, out)


def organization():
    """Brand identity. Deliberately says 'provides', never 'manufactures' -
    Praxera is not the manufacturer and must not be described as one."""
    return {
        "@type": "Organization",
        "@id": SITE + "/#organization",
        "name": "Praxera",
        "legalName": "Praxera of Vermont",
        "url": SITE + "/",
        "logo": {"@type": "ImageObject", "url": LOGO},
        "image": LOGO,
        "email": "info@praxerasupplements.com",
        "description": ("Praxera provides private label dietary supplements, from a "
                        "catalog of over 190 products, with label design and turnkey "
                        "production for brands building their own supplement lines."),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "929 Harvest Lane",
            "addressLocality": "Williston",
            "addressRegion": "VT",
            "postalCode": "05495",
            "addressCountry": "US",
        },
        "parentOrganization": {"@type": "Organization", "name": "FoodScience LLC"},
    }


def website():
    return {
        "@type": "WebSite",
        "@id": SITE + "/#website",
        "url": SITE + "/",
        "name": "Praxera",
        "publisher": {"@id": SITE + "/#organization"},
        "inLanguage": "en-US",
    }


def faqpage(url, qa):
    return {
        "@type": "FAQPage",
        "@id": url + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qa
        ],
    }


def block(graph):
    payload = {"@context": "https://schema.org", "@graph": graph}
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    # No "</script>" can survive inside a script element.
    body = body.replace('</', '<\\/')
    return '%s\n<script type="application/ld+json">%s</script>\n%s' % (START, body, END)


def splice(head, new):
    """Replace our own block if present, else append. Never disturb other content."""
    head = head or ''
    if START in head and END in head:
        return re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda m: new, head, flags=re.S)
    return (head.rstrip() + '\n' + new) if head.strip() else new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    pages = json.load(open('/tmp/prax.json'))
    planned, skipped = [], []
    for p in pages:
        slug = p['slug'] or ''
        name = slug or '(home)'
        if excluded(name):
            skipped.append(name)
            continue
        d = call('GET', '/cms/v3/pages/site-pages/%s/draft' % p['id'])
        url = SITE + '/' + slug if slug else SITE + '/'
        qa = []
        collect_qa(d, qa)
        # de-duplicate, preserve order
        seen, uniq = set(), []
        for q, a in qa:
            if q.lower() in seen:
                continue
            seen.add(q.lower())
            uniq.append((q, a))
        graph = []
        if not slug:                      # homepage carries the brand identity
            graph += [organization(), website()]
        if uniq:
            graph.append(faqpage(url, uniq))
        if graph:
            planned.append({'id': p['id'], 'slug': name, 'qa': len(uniq),
                            'graph': graph,
                            'head_before': len(d.get('headHtml') or ''),
                            'head_after': len(splice(d.get('headHtml'), block(graph)))})
        del d

    print('pages to receive markup : %d' % len(planned))
    print('FAQ pairs marked up     : %d' % sum(x['qa'] for x in planned))
    print('deliberately skipped    : %s' % ', '.join(sorted(skipped)))
    print()
    for x in sorted(planned, key=lambda y: -y['qa'])[:8]:
        print('   %-30s %2d Q&A   headHtml %d -> %d' %
              (x['slug'], x['qa'], x['head_before'], x['head_after']))
    if not apply:
        print('\nDRY RUN - nothing written. Re-run with --apply.')
        return

    ok = 0
    for x in planned:
        cur = call('GET', '/cms/v3/pages/site-pages/%s/draft' % x['id'])  # re-read at write time
        head = splice(cur.get('headHtml'), block(x['graph']))
        call('PATCH', '/cms/v3/pages/site-pages/%s/draft' % x['id'], {'headHtml': head})
        ok += 1
        del cur
    print('\napplied to %d pages' % ok)


if __name__ == '__main__':
    main()
