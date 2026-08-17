#!/usr/bin/env python3
"""Find partner decision-makers inside your own LinkedIn network.

This is the workaround for LinkedIn search being unavailable. Search is broken in
this Unipile workspace - Sales Navigator returns 401 expired_credentials, classic
search returns HTTP 200 with zero results, and every raw Voyager search endpoint
tried is rejected as malformed. But /users/relations lists your connections with
their headline and profile slug, and a headline almost always names the company
and the role. With ~14,700 connections across the HubSpot ecosystem, matching
those headlines against the partner list finds stakeholders without any search
API at all.

It only finds people you are already connected to - but that is exactly the
population worth approaching first about an acquisition, and a first-degree
connection additionally exposes contact_info.emails on profile lookup, so these
come with an email attached.

Pipeline:
  1. page every connection (limit 1000, so ~15 calls for 14,700)
  2. match each headline against partner company names
  3. keep the ones whose headline also reads as an owner/founder/CEO role
  4. optionally look up each match's profile for their email and confirmation

NOTE: cannot run inside the Claude sandbox. Unipile serves on port 16072 and the
sandbox proxy permits only standard ports, so the connection is reset. Run it
anywhere else and it works.

Usage:
    export UNIPILE_API_KEY=... UNIPILE_ACCOUNT_ID=...
    python3 scripts/find_partners_in_linkedin_network.py
    python3 scripts/find_partners_in_linkedin_network.py --enrich   # + emails
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
from source_ma_decision_makers import is_decision_maker  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS = os.path.join(REPO, "data", "hubspot_partners.csv")
OUT = os.path.join(REPO, "data", "partner_linkedin_connections.csv")
CACHE = os.path.join(os.environ.get("SCRATCH", "/tmp"), "li_relations.jsonl")

HOST = os.environ.get("UNIPILE_HOST", "api30.unipile.com:16072")

# Company-name tokens too generic to match a headline on. "Digital" or "Growth"
# would hit thousands of unrelated connections.
STOPWORDS = {
    "digital", "marketing", "agency", "group", "media", "studio", "labs",
    "consulting", "solutions", "partners", "partner", "growth", "inbound",
    "revenue", "sales", "creative", "company", "the", "and", "for", "hub",
    "hubspot", "crm", "data", "web", "tech", "technology", "software",
    "services", "systems", "global", "international", "online", "interactive",
    "communications", "collective", "ventures", "consultancy", "advisors",
    "strategy", "strategies", "works", "works", "world", "team", "house",
    "factory", "studios", "labs", "co", "inc", "ltd", "llc", "gmbh", "bv",
}


def get(path: str, tries: int = 5) -> dict:
    key = os.environ.get("UNIPILE_API_KEY", "")
    if not key:
        raise SystemExit("set UNIPILE_API_KEY")
    for attempt in range(tries):
        req = urllib.request.Request(f"https://{HOST}{path}", headers={
            "X-API-KEY": key, "accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()[:200]
            if exc.code == 429:
                time.sleep(min(5 * (attempt + 1), 60))
                continue
            if exc.code in (400, 401, 403, 404, 422):
                return {"_error": f"HTTP {exc.code}: {body}"}
            time.sleep(min(2 ** attempt, 20))
        except (urllib.error.URLError, TimeoutError) as exc:
            # In the Claude sandbox this is where it dies: port 16072 is not
            # permitted by the outbound proxy, so the connection is reset.
            if attempt == tries - 1:
                return {"_error": f"network: {exc}"}
            time.sleep(min(2 ** attempt, 20))
    return {"_error": "gave up"}


def all_relations(account: str) -> list[dict]:
    """Every connection, cached so a re-run costs nothing."""
    if os.path.exists(CACHE):
        rows = [json.loads(l) for l in open(CACHE, encoding="utf-8") if l.strip()]
        print(f"  loaded {len(rows)} connections from cache")
        return rows
    rows, cursor = [], None
    with open(CACHE, "w", encoding="utf-8") as fh:
        while True:
            path = (f"/api/v1/users/relations?account_id={account}&limit=1000"
                    + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
            page = get(path)
            if page.get("_error"):
                print(f"  ! {page['_error']}", file=sys.stderr)
                break
            items = page.get("items") or []
            for it in items:
                fh.write(json.dumps(it) + "\n")
            rows.extend(items)
            cursor = page.get("cursor")
            print(f"  connections: {len(rows)}", end="\r", flush=True)
            if not cursor or not items:
                break
            time.sleep(1.0)  # a real LinkedIn session - do not hammer it
    print(f"  connections: {len(rows)} total")
    return rows


def name_keys(company: str) -> list[str]:
    """Distinctive lowercase tokens from a company name, for headline matching."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9&'-]{2,}", company or "")
    out = [w.lower() for w in words if w.lower() not in STOPWORDS and len(w) >= 4]
    # A single distinctive word is enough ("TRooInbound"), but a name made only
    # of stopwords ("Digital Growth Agency") yields nothing and is skipped
    # rather than matched loosely.
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enrich", action="store_true",
                    help="look up each match's profile for their email")
    ap.add_argument("--tiers", nargs="+",
                    default=["elite", "diamond", "platinum", "gold"])
    args = ap.parse_args()

    account = os.environ.get("UNIPILE_ACCOUNT_ID", "")
    if not account:
        raise SystemExit("set UNIPILE_ACCOUNT_ID")

    partners = [p for p in csv.DictReader(open(PARTNERS, encoding="utf-8-sig"))
                if p["domain"] and p["tier"] in args.tiers]
    index: dict[str, list[dict]] = {}
    for p in partners:
        for k in name_keys(p["company_name"]):
            index.setdefault(k, []).append(p)
    print(f"partners in scope: {len(partners)}  "
          f"distinctive name tokens: {len(index)}\n")

    print("paging your LinkedIn connections:")
    rels = all_relations(account)
    if not rels:
        print("no connections retrieved - see the error above", file=sys.stderr)
        return 1

    rows = []
    for r in rels:
        head = (r.get("headline") or "")
        low = head.lower()
        hits = []
        for token, plist in index.items():
            if token in low:
                hits.extend(plist)
        if not hits:
            continue
        # Prefer the strongest tier when a headline matches several partners.
        rank = {"elite": 0, "diamond": 1, "platinum": 2, "gold": 3}
        hits.sort(key=lambda p: rank.get(p["tier"], 9))
        p = hits[0]
        rows.append({
            "name": f"{r.get('first_name','')} {r.get('last_name','')}".strip(),
            "headline": head[:170],
            "is_decision_maker": "YES" if is_decision_maker(head) else "",
            "partner_company": p["company_name"],
            "partner_domain": p["domain"],
            "tier": p["tier"],
            "country": p["country"],
            "linkedin_url": r.get("public_profile_url") or "",
            "slug": r.get("public_identifier") or "",
            "connected_since": time.strftime(
                "%Y-%m-%d", time.gmtime((r.get("created_at") or 0) / 1000))
            if r.get("created_at") else "",
            "email": "",
            "match_count": len(hits),
        })

    dm = [r for r in rows if r["is_decision_maker"]]
    print(f"\nconnections whose headline names a partner: {len(rows)}")
    print(f"  of those, owner/founder/CEO-level          {len(dm)}")
    print(f"  distinct partner agencies                  "
          f"{len({r['partner_domain'] for r in dm})}")

    if args.enrich and dm:
        print(f"\nlooking up {len(dm)} profiles for emails "
              f"(first-degree connections expose contact_info):")
        for i, r in enumerate(dm, 1):
            prof = get(f"/api/v1/users/{urllib.parse.quote(r['slug'])}"
                       f"?account_id={account}")
            mails = ((prof.get("contact_info") or {}).get("emails") or [])
            r["email"] = mails[0] if mails else ""
            print(f"  [{i}/{len(dm)}] {r['name'][:28]:28s} "
                  f"{r['email'] or '(no email exposed)'}")
            time.sleep(1.5)

    rows.sort(key=lambda r: (not r["is_decision_maker"],
                             {"elite": 0, "diamond": 1, "platinum": 2,
                              "gold": 3}.get(r["tier"], 9), r["partner_company"]))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT} ({len(rows)} rows)")
    if args.enrich:
        print(f"  with an email: {sum(1 for r in rows if r['email'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
