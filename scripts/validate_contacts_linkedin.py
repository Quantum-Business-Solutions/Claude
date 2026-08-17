#!/usr/bin/env python3
"""Validate sourced contacts against their live LinkedIn profile via Unipile.

This closes the biggest quality gap in the scraped contacts. A name lifted from a
team page proves only that the page mentioned them; the live profile proves they
still hold that role at that company today. Three checks per person:

  title_ok    the profile headline still shows an owner/founder/CEO-type role
  company_ok  the headline or the profile's own websites reference the partner
              company - this is what catches someone who has since left
  reachable   network distance and shared connections, which is warm-intro intel
              for an acquisition approach rather than a data-quality signal

Only profile lookup is used. LinkedIn *search* through this Unipile workspace does
not work - Sales Navigator returns 401 expired_credentials and classic search
returns HTTP 200 with zero results for every query on every account, because the
connected accounts only have a _MESSAGING source provisioned. So this can verify
people we already have a profile URL for, and cannot discover new ones.

A first-degree connection additionally exposes contact_info.emails, so running
this over people Shawn already knows is also an email source - Nikhil Jani's
profile returned an address on a different domain than the one scraped from his
site, which is a discrepancy worth resolving before mailing him.

NOTE ON THIS ENVIRONMENT: Unipile serves on port 16072, and the sandbox's
outbound proxy only permits standard ports, so this script cannot run here - the
connection is reset before it leaves. It runs fine anywhere without that
restriction. In this session the same lookups have to go through the Unipile MCP
tool, one profile per call.

Read-only against HubSpot; read-only against LinkedIn.

Usage:
    export UNIPILE_API_KEY=... UNIPILE_HOST=api30.unipile.com:16072
    export UNIPILE_ACCOUNT_ID=...
    python3 scripts/validate_contacts_linkedin.py --limit 20
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from domainutil import registrable_domain  # noqa: E402
from source_ma_decision_makers import is_decision_maker  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(REPO, "data", "ma_decision_makers.csv")
OUT = os.path.join(REPO, "data", "linkedin_validation.csv")
CACHE = os.path.join(os.environ.get("SCRATCH", "/tmp"), "li_profiles.jsonl")

SLUG_RE = re.compile(r"linkedin\.com/in/([^/?#]+)", re.I)
# Words in a headline that mean the person no longer runs the company.
FORMER = re.compile(r"\b(former|ex-|retired|previously|advisor to)\b", re.I)


def host() -> str:
    return os.environ.get("UNIPILE_HOST", "api30.unipile.com:16072")


def get(path: str, tries: int = 4) -> dict:
    key = os.environ.get("UNIPILE_API_KEY", "")
    if not key:
        raise RuntimeError("set UNIPILE_API_KEY")
    url = f"https://{host()}{path}"
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={
            "X-API-KEY": key, "accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()[:200]
            # 404 = no such profile; retrying will not help.
            if exc.code in (400, 401, 403, 404, 422):
                return {"_error": f"HTTP {exc.code}", "_body": body}
            time.sleep(min(2 ** attempt, 15))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2 ** attempt, 15))
    return {"_error": "gave up"}


def load_cache() -> dict:
    out = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    out[rec["slug"]] = rec["profile"]
                except (json.JSONDecodeError, KeyError):
                    continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=1.5,
                    help="delay between lookups; this drives a real LinkedIn "
                         "session, so do not hammer it")
    args = ap.parse_args()

    account = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not account:
        print("set UNIPILE_ACCOUNT_ID", file=sys.stderr)
        return 1

    rows = [r for r in csv.DictReader(open(IN, encoding="utf-8-sig"))
            if SLUG_RE.search(r.get("linkedin_url") or "")]
    if args.limit:
        rows = rows[:args.limit]
    print(f"contacts with a LinkedIn URL to validate: {len(rows)}\n")

    cache = load_cache()
    out_rows, stats = [], {"confirmed": 0, "title_unstated": 0,
                           "title_changed": 0, "company_mismatch": 0,
                           "not_found": 0, "error": 0}
    for i, r in enumerate(rows, 1):
        slug = SLUG_RE.search(r["linkedin_url"]).group(1).lower()
        if slug in cache:
            prof = cache[slug]
        else:
            prof = get(f"/api/v1/users/{urllib.parse.quote(slug)}"
                       f"?account_id={account}")
            with open(CACHE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"slug": slug, "profile": prof}) + "\n")
            time.sleep(args.sleep)

        if prof.get("_error"):
            verdict = "not_found" if "404" in prof["_error"] else "error"
            stats[verdict] += 1
            out_rows.append({**base(r, slug), "verdict": verdict,
                             "detail": prof.get("_error", "")})
            print(f"[{i}/{len(rows)}] {slug[:30]:30s} {verdict}")
            continue

        headline = prof.get("headline") or ""
        name = f"{prof.get('first_name','')} {prof.get('last_name','')}".strip()
        # The partner domain should appear in the profile's own websites, or the
        # company name in the headline. Either is solid evidence of employment.
        sites = {registrable_domain(w) for w in (prof.get("websites") or [])}
        dom = r["company_domain"].lower()
        company_words = [w.lower() for w in re.findall(
            r"[A-Za-z]{4,}", r.get("partner_company") or "")]
        company_ok = dom in sites or any(
            w in headline.lower() for w in company_words)
        title_ok = is_decision_maker(headline) and not FORMER.search(headline)

        # An absent title is not a changed title. Plenty of founders - European
        # ones especially - write a value-proposition headline with no role in
        # it at all ("Helping B2B companies optimize their sales processes"),
        # and Christian Retz at Divia reads exactly that way while divia.de sits
        # right there in his profile websites. Treating that as a departure
        # would discard a good contact, so only an explicit former/ex- marker
        # counts as a change and everything else is merely unconfirmed.
        if not company_ok:
            verdict = "company_mismatch"
        elif FORMER.search(headline):
            verdict = "title_changed"
        elif not title_ok:
            verdict = "title_unstated"
        else:
            verdict = "confirmed"
        stats[verdict] += 1
        out_rows.append({
            **base(r, slug), "verdict": verdict,
            "detail": "", "live_name": name, "live_headline": headline[:180],
            "live_location": prof.get("location") or "",
            "profile_websites": "; ".join(sorted(s for s in sites if s)),
            "network_distance": prof.get("network_distance") or "",
            "shared_connections": prof.get("shared_connections_count") or 0,
            "followers": prof.get("follower_count") or 0,
            "is_premium": "YES" if prof.get("is_premium") else "",
        })
        print(f"[{i}/{len(rows)}] {slug[:28]:28s} {verdict:17s} "
              f"{headline[:56]}")

    cols: list[str] = []
    for r in out_rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out_rows)

    print(f"\n{stats}")
    warm = [r for r in out_rows
            if r.get("network_distance") in ("FIRST_DEGREE", "SECOND_DEGREE")]
    print(f"reachable within 2 degrees on LinkedIn: {len(warm)}")
    first = [r for r in out_rows if r.get("network_distance") == "FIRST_DEGREE"]
    if first:
        print(f"  already a 1st-degree connection: {len(first)} -> "
              + ", ".join(r["name"] for r in first[:8]))
    print(f"wrote {OUT}")
    return 0


def base(r: dict, slug: str) -> dict:
    return {"name": f"{r['first_name']} {r['last_name']}".strip(),
            "sourced_title": r.get("job_title", ""),
            "partner_company": r.get("partner_company", ""),
            "company_domain": r.get("company_domain", ""),
            "tier": r.get("tier", ""), "source": r.get("source", ""),
            "slug": slug}


if __name__ == "__main__":
    raise SystemExit(main())
