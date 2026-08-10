#!/usr/bin/env python3
"""Find agency owners/founders from the partner's own website.

Why this is the primary source rather than a fallback: these are small agencies,
and their leadership is on their own /about or /team page with a LinkedIn link
next to it. ZoomInfo often has the bench and not the top of house - it has 24
contacts at MakeWebBetter and neither co-founder, and ClearPivot's accountant but
not its principal. A team page has both, plus the LinkedIn URL we actually want.

Costs nothing per company: plain HTTPS, no API key, no credits.

Approach is deliberately recall-first. Rather than trying to parse arbitrary team
-card markup into clean records, it collects every LinkedIn profile link on the
leadership pages together with the text around it, then scores that context for
owner language. A human (or a later pass) confirms; the expensive part - knowing
which page to read and which profile is the owner - is what this automates.

Usage:
    python3 scripts/scrape_partner_leadership.py --domains clearpivot.com ...
    python3 scripts/scrape_partner_leadership.py --tiers diamond --limit 50
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import gzip
import html
import io
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from source_ma_decision_makers import is_decision_maker, targets  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "partner_leadership_scraped.csv")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# Paths that hold leadership, in rough order of how often they do. Matched
# against the href, so /about-us/our-team and /en/team both hit.
TEAM_HINTS = ("team", "about", "leadership", "who-we-are", "our-story",
              "people", "company", "founders", "management", "meet")

# Titles worth surfacing. Kept separate from is_decision_maker's screen because
# web copy is looser than a CRM job title - "Founder & Chief Coffee Drinker"
# should still match.
#
# Bare "partner" is deliberately absent. Every company in this list is a HubSpot
# Solutions Partner and says so on every page, so matching it produces a hit on
# all 1,424 sites and means nothing. "Managing partner" is specific enough.
OWNER_WORDS = re.compile(
    r"\b(co-?founders?|founders?|co-?owner|owner|principal|president|ceo|"
    r"chief executive(?:\s+officer)?|managing director|managing partner|"
    r"chairman|chairwoman|proprietor)\b", re.I)

LINKEDIN_RE = re.compile(
    r"""https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9\-_%.]+)""", re.I)
MAILTO_RE = re.compile(r"mailto:([^\"'?>\s]+@[^\"'?>\s]+)", re.I)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)

# A LinkedIn URN slug is per-viewer noise, never a durable identifier.
URN_SLUG = re.compile(r"^AC[waoQ][A-Za-z0-9_-]{10,}$", re.I)

# Personal names, roughly: two or three capitalised words. Deliberately loose;
# false positives are cheap here because the title context does the real work.
NAME_RE = re.compile(
    r"\b([A-Z][a-z'À-ɏ-]{1,20}(?:\s+[A-Z][a-z'À-ɏ-]{1,20}){1,2})\b")

# Firstname Lastname only. Used where the match must end exactly at the title,
# because there the greedy three-word form reaches back into the previous phrase.
NAME2 = r"\b([A-Z][a-z'À-ɏ-]{1,20}\s+[A-Z][a-z'À-ɏ-]{1,20})"

# Words that look like names by shape but never are, so they don't get proposed
# as the owner of an agency.
NOT_NAME = {"Privacy Policy", "Terms Of", "Contact Us", "About Us", "Our Team",
            "Read More", "Learn More", "Case Studies", "Get Started",
            "Book A", "Cookie Policy", "All Rights", "United States",
            "New York", "Los Angeles", "Sign Up", "Log In", "Meet The"}


def fetch(url: str, timeout: int = 15) -> tuple[str, str]:
    """GET a page, returning (text, final_url) and handling gzip/deflate.

    The final URL matters: most of these domains redirect example.com ->
    www.example.com, and resolving links against the pre-redirect URL makes
    every internal link look off-site, so no team page is ever discovered.
    """
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(3_000_000)
        enc = (r.headers.get("Content-Encoding") or "").lower()
        final = r.geturl()
    if enc == "gzip":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    elif enc == "deflate":
        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
    return raw.decode("utf-8", errors="replace"), final


def visible_text(page: str) -> str:
    page = TAG_RE.sub(" ", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page))


def team_urls(base: str, page: str) -> list[str]:
    """Leadership-page candidates, best first."""
    out: list[tuple[int, str]] = []
    seen = set()
    for href in re.findall(r"""href\s*=\s*["']([^"']+)["']""", page, re.I):
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        absolute = urllib.parse.urljoin(base, href)
        if urllib.parse.urlparse(absolute).netloc != urllib.parse.urlparse(base).netloc:
            continue
        absolute = absolute.split("#")[0].rstrip("/")
        path = urllib.parse.urlparse(absolute).path.lower()
        if not path or absolute in seen:
            continue
        score = sum(2 if h in path.split("/")[-1] else 1
                    for h in TEAM_HINTS if h in path)
        if not score:
            continue
        # Deep blog posts about "our team culture" are not the team page.
        if path.count("/") > 3 or "/blog/" in path:
            score -= 2
        if score <= 0:
            continue
        seen.add(absolute)
        out.append((score, absolute))
    out.sort(key=lambda t: (-t[0], len(t[1])))
    return [u for _, u in out[:4]]


def harvest(domain: str, url: str, page: str, company: str) -> list[dict]:
    """Owner-titled people on the page, anchored on the title text.

    Anchoring on titles rather than on LinkedIn links is the whole trick. Most of
    these team pages name the founder in plain text and link nothing: ClearPivot's
    /team reads "Chris Strom Principal Chris Strom founded ClearPivot back in
    2009" and contains no profile link anywhere. The name is the valuable part -
    the LinkedIn URL can be resolved from a name plus a company afterwards.
    """
    text = visible_text(page)
    linked = {}
    for m in LINKEDIN_RE.finditer(page):
        slug = urllib.parse.unquote(m.group(1)).strip(".").lower()
        if slug and not URN_SLUG.match(slug):
            window = visible_text(page[max(0, m.start() - 400): m.end() + 400])
            linked[slug] = window

    company_words = {w.lower() for w in re.findall(r"[A-Za-z]{3,}", company)}
    found: dict[str, dict] = {}
    for m in OWNER_WORDS.finditer(text):
        title = m.group(0)
        # "Chris Strom Principal" is the dominant layout, so look behind first;
        # "Principal: Chris Strom" and "Founded by Chris Strom" look ahead.
        # Tight windows on purpose. A wide window reaches into the neighbouring
        # team card and splices two people together ("Greg Lukach Chris"), or
        # picks up the customer quoted in a testimonial three lines down.
        lead = text[max(0, m.start() - 34):m.start()]
        # Only a name that runs right up to the title counts; "...our work. Jane
        # Doe is a client. CEO" must not match Jane Doe.
        # Exactly two words, not "two or three": the greedy three-word form
        # swallows the tail of the preceding phrase, giving "Business
        # Development Neal Lappe" -> "Development Neal Lappe".
        lead_m = re.search(NAME2 + r"[\s,–—:|/-]{0,4}$", lead)
        before = [lead_m.group(1)] if lead_m else []
        trail_m = re.match(r"^[\s,–—:|/-]{0,4}(?:of|at|is|for)?\s*"
                           + NAME_RE.pattern, text[m.end():m.end() + 40])
        after = [trail_m.group(1)] if trail_m else []
        name = ""
        for candidate in (before[-1:] + after[:1]):
            c = candidate.strip()
            if c in NOT_NAME or OWNER_WORDS.search(c):
                continue
            # The agency's own name sits next to owner words constantly
            # ("Founder of ClearPivot"), and is not a person.
            if {w.lower() for w in c.split()} & company_words:
                continue
            name = c
            break
        if not name:
            continue
        rec = found.setdefault(name.lower(), {
            "domain": domain, "name": name, "titles": set(),
            "linkedin_url": "", "name_matches_slug": "", "source_url": url})
        rec["titles"].add(title.title())
        # If the page does link profiles, attach the one whose slug matches.
        if not rec["linkedin_url"]:
            key = re.sub(r"[^a-z]", "", name.lower())
            for slug in linked:
                bare = re.sub(r"[^a-z]", "", slug)
                if key and (key in bare or bare in key):
                    rec["linkedin_url"] = f"https://www.linkedin.com/in/{slug}"
                    rec["name_matches_slug"] = "YES"
                    break
    return list(found.values())


def emails(domain: str, page: str) -> list[str]:
    out = []
    for e in list(MAILTO_RE.findall(page)) + EMAIL_RE.findall(visible_text(page)):
        e = html.unescape(e).strip().lower().rstrip(".,;")
        # Only the agency's own addresses; anything else is a vendor or client.
        if e.endswith("@" + domain) and e not in out:
            out.append(e)
    return out


def one_domain(p: dict) -> dict:
    domain = p["domain"]
    result = {"domain": domain, "company": p.get("company_name", ""),
              "tier": p.get("tier", ""), "country": p.get("country", ""),
              "status": "", "people": [], "emails": [], "pages": 0}
    home = base = ""
    for candidate in (f"https://{domain}", f"https://www.{domain}"):
        try:
            home, base = fetch(candidate)
            break
        except Exception:  # noqa: BLE001 - any failure means try the next form
            continue
    if not home:
        result["status"] = "unreachable"
        return result
    pages = [(base, home)]
    for url in team_urls(base, home):
        try:
            page, _ = fetch(url)
            pages.append((url, page))
        except Exception:  # noqa: BLE001
            continue
    result["pages"] = len(pages)
    people: dict[str, dict] = {}
    for url, page in pages:
        for rec in harvest(domain, url, page, result["company"] or domain):
            prior = people.get(rec["name"].lower())
            if prior:
                prior["titles"] |= rec["titles"]
                if rec["linkedin_url"] and not prior["linkedin_url"]:
                    prior["linkedin_url"] = rec["linkedin_url"]
                    prior["name_matches_slug"] = rec["name_matches_slug"]
            else:
                people[rec["name"].lower()] = rec
        for e in emails(domain, page):
            if e not in result["emails"]:
                result["emails"].append(e)
    # Owner-titled profiles first, then those whose name matches their slug.
    ranked = sorted(people.values(),
                    key=lambda r: (not r["titles"], not r["linkedin_url"]))
    result["people"] = ranked
    result["status"] = "ok" if ranked else "no_profiles_found"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", nargs="*", default=[])
    ap.add_argument("--tiers", nargs="+",
                    default=["diamond", "platinum", "gold"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    if args.domains:
        pool = targets(tuple(args.tiers), 0)
        by_dom = {p["domain"]: p for p in pool}
        todo = [by_dom.get(d, {"domain": d}) for d in args.domains]
    else:
        todo = targets(tuple(args.tiers), args.limit)
    print(f"scraping {len(todo)} partner sites with {args.workers} workers\n")

    COLS = ["domain", "company", "tier", "country", "name", "titles",
            "is_owner", "name_matches_slug", "linkedin_url", "source_url",
            "site_emails"]
    rows, stats = [], {"ok": 0, "unreachable": 0, "no_profiles_found": 0}
    with_owner = 0
    # Written as results arrive: a full pass over 1,424 sites takes ~20 minutes
    # and a failure near the end must not discard everything before it.
    out_fh = open(OUT, "w", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(out_fh, fieldnames=COLS)
    writer.writeheader()
    with concurrent.futures.ThreadPoolExecutor(args.workers) as ex:
        for i, res in enumerate(ex.map(one_domain, todo), 1):
            stats[res["status"]] = stats.get(res["status"], 0) + 1
            owners = [p for p in res["people"] if p["titles"]]
            if owners:
                with_owner += 1
            print(f"[{i}/{len(todo)}] {res['domain'][:26]:26s} "
                  f"{res['status']:18s} pages={res['pages']} "
                  f"owners={len(owners)} emails={len(res['emails'])}")
            for p in owners[:4]:
                print(f"      {p['name'] or '(name unresolved)':26s} "
                      f"{'/'.join(sorted(p['titles']))[:34]:34s} {p['linkedin_url']}")
            for p in res["people"]:
                row = {
                    "domain": res["domain"], "company": res["company"],
                    "tier": res["tier"], "country": res["country"],
                    "name": p["name"], "titles": "/".join(sorted(p["titles"])),
                    "is_owner": "YES" if p["titles"] else "",
                    "name_matches_slug": p["name_matches_slug"],
                    "linkedin_url": p["linkedin_url"],
                    "source_url": p["source_url"],
                    "site_emails": "; ".join(res["emails"][:5]),
                }
                rows.append(row)
                writer.writerow(row)
            out_fh.flush()
    out_fh.close()
    n = len(todo)
    print(f"\n{stats}")
    print(f"companies with at least one owner-titled profile: "
          f"{with_owner}/{n} ({with_owner * 100 // max(n, 1)}%)")
    print(f"wrote {OUT} ({len(rows)} profiles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
