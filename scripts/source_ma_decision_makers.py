#!/usr/bin/env python3
"""Source owner/CEO/president contacts for partner agencies via the ZoomInfo API.

Two stages, deliberately split by cost:

1. /search/contact per company domain - FREE. Filtered to C-level and board
   seniority, which is the filter that actually works; passing jobTitle together
   with companyWebsite silently returns zero results.
2. /enrich/contact in batches of 10 - BILLS BULK CREDITS. Only the people who
   survive the decision-maker screen get enriched, and only once: results are
   appended to a resume cache so an interrupted run never re-buys a contact.

Output is data/ma_decision_makers.csv, the input format that
load_ma_contacts_to_hubspot.py expects.

Usage:
    # credentials in the environment only - see scripts/zoominfo_api.py
    python3 scripts/source_ma_decision_makers.py --tiers diamond platinum gold
    python3 scripts/source_ma_decision_makers.py --limit 40 --no-enrich
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zoominfo_api import ZoomInfo, ZoomInfoError  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(REPO, "data")
OUT = os.path.join(D, "ma_decision_makers.csv")
SEARCH_CACHE = os.path.join(D, "zi_search.cache.jsonl")
ENRICH_CACHE = os.path.join(D, "zi_enrich.cache.jsonl")

# Titles matched with word boundaries throughout. Plain substring matching is a
# trap here: "managing direCTOr" contains "cto", so a naive exclusion list
# silently discards every Managing Director in the file.

# Holds equity. Outranks any functional exclusion below - a "Founder & CTO" can
# still sell the business.
EQUITY = r"owner|founder|co-?founder|chair(man|woman|person)?|managing partner"

# Runs the company. Counts unless a functional exclusion also matches.
EXEC = (r"chief executive|ceo|president|managing director|"
        r"managing partner|principal")

# Runs a function, not the cap table - not worth a credit on its own.
FUNCTIONAL = (r"cto|chief technology|cfo|chief financial|cmo|chief marketing|"
              r"chief revenue|cro|chief operating|coo|chief of staff|"
              r"chief people|chief product|ciso|chief information|"
              r"consultant|advisor|assistant|deputy|vice")

_EQUITY = re.compile(rf"\b(?:{EQUITY})\b", re.I)
_EXEC = re.compile(rf"\b(?:{EXEC})\b", re.I)
_FUNCTIONAL = re.compile(rf"\b(?:{FUNCTIONAL})\b", re.I)

ENRICH_FIELDS = ["firstName", "lastName", "email", "jobTitle",
                 "managementLevel", "companyName", "zoominfoCompanyId",
                 "externalUrls", "phone", "mobilePhone",
                 "directPhoneDoNotCall", "mobilePhoneDoNotCall",
                 "contactAccuracyScore", "validDate", "lastUpdatedDate"]

COLUMNS = ["first_name", "last_name", "email", "linkedin_url", "job_title",
           "role", "company_domain", "partner_company", "tier", "country",
           "phone", "mobile_phone", "mobile_dnc", "direct_dnc", "source",
           "accuracy", "valid_date", "zi_person_id"]


def is_decision_maker(title: str) -> bool:
    t = title or ""
    if _EQUITY.search(t):
        return True
    return bool(_EXEC.search(t)) and not _FUNCTIONAL.search(t)


def load_cache(path: str) -> dict:
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a run killed mid-write leaves one short line
                out[rec["key"]] = rec["value"]
    return out


def append_cache(path: str, key: str, value) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"key": key, "value": value}) + "\n")
        fh.flush()


def best_linkedin(entry: dict) -> str:
    """Pick the vanity LinkedIn URL, never the opaque URN form.

    ZoomInfo returns both; the URN is per-viewer and unusable as a key.
    """
    for u in entry.get("externalUrls") or []:
        url = u.get("url") or ""
        if "linkedin.com/in/" not in url:
            continue
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if not slug.startswith(("ACw", "ACo", "ACa", "ACQ")):
            return url
    return ""


def targets(tiers: tuple[str, ...], limit: int) -> list[dict]:
    """Partner agencies in the given tiers that still lack a decision-maker."""
    partners = list(csv.DictReader(
        open(os.path.join(D, "hubspot_partners.csv"), encoding="utf-8-sig")))
    have = set()
    pc = os.path.join(D, "partner_contacts.csv")
    if os.path.exists(pc):
        for c in csv.DictReader(open(pc, encoding="utf-8-sig")):
            if is_decision_maker(c.get("job_title", "")):
                have.add(c["partner_domain"])
    dm = os.path.join(D, "acquisition_decision_makers.csv")
    if os.path.exists(dm):
        have |= {r["domain"] for r in
                 csv.DictReader(open(dm, encoding="utf-8-sig"))}
    rows = [p for p in partners
            if p["tier"] in tiers and p["domain"] and p["domain"] not in have]
    rank = {"diamond": 0, "platinum": 1, "gold": 2}
    rows.sort(key=lambda p: (rank.get(p["tier"], 9),
                             -int(p["review_count"] or 0)))
    return rows[:limit] if limit else rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", nargs="+",
                    default=["diamond", "platinum", "gold"])
    ap.add_argument("--limit", type=int, default=0,
                    help="cap the number of companies (0 = all)")
    ap.add_argument("--no-enrich", action="store_true",
                    help="run the free search stage only, spend no credits")
    args = ap.parse_args()

    todo = targets(tuple(args.tiers), args.limit)
    print(f"companies to source: {len(todo)}")
    try:
        zi = ZoomInfo()
        zi.token
    except ZoomInfoError as exc:
        print(f"ZoomInfo auth unavailable: {exc}", file=sys.stderr)
        return 1

    # ---- stage 1: free search ------------------------------------------
    scache = load_cache(SEARCH_CACHE)
    hits: list[dict] = []
    for i, p in enumerate(todo, 1):
        dom = p["domain"]
        if dom in scache:
            data = scache[dom]
        else:
            try:
                res = zi.search_contacts(
                    companyWebsite=dom, managementLevel="C-Level,Board Member",
                    rpp=25, page=1)
                data = res.get("data") or []
            except ZoomInfoError as exc:
                print(f"\n  ! search {dom}: {exc}", file=sys.stderr)
                data = []
            append_cache(SEARCH_CACHE, dom, data)
            time.sleep(0.08)
        for c in data:
            if is_decision_maker(c.get("jobTitle") or ""):
                hits.append({"partner": p, "contact": c})
        if i % 25 == 0 or i == len(todo):
            print(f"  searched {i}/{len(todo)}, decision-makers so far "
                  f"{len(hits)}", end="\r", flush=True)
    covered = len({h["partner"]["domain"] for h in hits})
    print(f"\ndecision-makers found: {len(hits)} across {covered} companies "
          f"({covered * 100 // max(len(todo), 1)}% of targets)")
    if args.no_enrich:
        print("--no-enrich: stopping before any credit is spent")
        return 0

    # ---- stage 2: billed enrichment ------------------------------------
    ecache = load_cache(ENRICH_CACHE)
    need = [h for h in hits if str(h["contact"]["id"]) not in ecache]
    print(f"enriching {len(need)} contacts ({len(hits) - len(need)} cached)")
    for chunk in (need[i:i + 10] for i in range(0, len(need), 10)):
        inputs = [{"personId": str(h["contact"]["id"])} for h in chunk]
        try:
            res = zi.enrich_contacts(inputs, ENRICH_FIELDS)
        except ZoomInfoError as exc:
            print(f"  ! enrich batch: {exc}", file=sys.stderr)
            continue
        results = (res.get("data") or {}).get("result") or []
        for item in results:
            for entry in item.get("data") or []:
                pid = str(entry.get("id") or "")
                if pid:
                    ecache[pid] = entry
                    append_cache(ENRICH_CACHE, pid, entry)
        time.sleep(0.15)

    rows = []
    for h in hits:
        e = ecache.get(str(h["contact"]["id"]))
        if not e:
            continue
        p = h["partner"]
        rows.append({
            "first_name": e.get("firstName") or "",
            "last_name": e.get("lastName") or "",
            "email": e.get("email") or "",
            "linkedin_url": best_linkedin(e),
            "job_title": e.get("jobTitle") or "",
            "role": "",
            "company_domain": p["domain"],
            "partner_company": p["company_name"],
            "tier": (p["tier"] or "").title(),
            "country": p["country"],
            "phone": e.get("phone") or "",
            "mobile_phone": e.get("mobilePhone") or "",
            "mobile_dnc": "Y" if e.get("mobilePhoneDoNotCall") else "",
            "direct_dnc": "Y" if e.get("directPhoneDoNotCall") else "",
            "source": "ZoomInfo",
            "accuracy": str(e.get("contactAccuracyScore") or "").split(".")[0],
            "valid_date": (e.get("validDate") or "")[:10],
            "zi_person_id": str(e.get("id") or ""),
        })

    rank = {"Diamond": 0, "Platinum": 1, "Gold": 2}
    rows.sort(key=lambda r: (rank.get(r["tier"], 9), r["partner_company"]))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}: {len(rows)} decision-makers")
    print(f"  with email     {sum(1 for r in rows if r['email'])}")
    print(f"  with LinkedIn  {sum(1 for r in rows if r['linkedin_url'])}")
    print(f"  neither        {sum(1 for r in rows if not r['email'] and not r['linkedin_url'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
