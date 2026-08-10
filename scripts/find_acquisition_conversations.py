#!/usr/bin/env python3
"""Find past acquisition conversations in HubSpot and flag which were with partners.

Searches meeting, email, note and call bodies for acquisition language, then
resolves each hit's associated company/contact and marks whether that company is
in the HubSpot Solutions Partner Directory export.

Keyword-first rather than association-first: acquisition talk is rare, so
searching content narrows to a handful of records, whereas walking associations
from 7,390 partner companies would mean tens of thousands of calls.

Read-only.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/find_acquisition_conversations.py
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.hubapi.com"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS = os.path.join(REPO, "data", "hubspot_partners.csv")
OUT = os.path.join(REPO, "data", "acquisition_conversations.csv")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from domainutil import registrable_domain  # noqa: E402

# Wildcards let CONTAINS_TOKEN match acquisition/acquire/acquiring etc.
KEYWORDS = [
    "acquisi*", "acquire*", "acquiring", "acquisition", "merger", "m&a",
    "buyout", "buy-out", "tuck-in", "tuckin", "roll-up", "rollup",
    "letter of intent", "valuation", "due diligence", "earnout", "earn-out",
    "selling your agency", "sell your agency", "sell the agency",
    "exit strategy", "book of business", "divest", "majority stake",
]

# object type -> (searchable text properties, extra properties to return)
OBJECTS = {
    "meetings": (["hs_meeting_title", "hs_meeting_body"],
                 ["hs_meeting_start_time", "hs_timestamp", "hubspot_owner_id",
                  "hs_meeting_outcome"]),
    "emails": (["hs_email_subject", "hs_email_text"],
               ["hs_timestamp", "hs_email_direction", "hubspot_owner_id"]),
    "notes": (["hs_note_body"], ["hs_timestamp", "hubspot_owner_id"]),
    "calls": (["hs_call_title", "hs_call_body"],
              ["hs_timestamp", "hs_call_direction", "hubspot_owner_id"]),
}


def call(token: str, path: str, payload=None, method="POST"):
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(6):
        req = urllib.request.Request(
            f"{API}{path}", data=data, method=method,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** attempt, 20))
                continue
            raise RuntimeError(f"HTTP {e.code} {path}: {body}") from e
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"gave up on {path}")


def search_keyword(token: str, obj: str, prop: str, kw: str,
                   props: list[str]) -> list[dict]:
    hits, after = [], None
    while True:
        body = {
            "limit": 100,
            "filterGroups": [{"filters": [
                {"propertyName": prop, "operator": "CONTAINS_TOKEN",
                 "value": kw}]}],
            "properties": props,
        }
        if after:
            body["after"] = after
        try:
            page = call(token, f"/crm/v3/objects/{obj}/search", body)
        except RuntimeError as exc:
            # Some text properties reject CONTAINS_TOKEN; skip rather than abort.
            print(f"    ! {obj}.{prop} '{kw}': {exc}", file=sys.stderr)
            return hits
        hits.extend(page.get("results", []))
        after = page.get("paging", {}).get("next", {}).get("after")
        if not after or len(hits) >= 300:
            break
        time.sleep(0.12)
    return hits


def associated(token: str, obj: str, oid: str, to: str) -> list[str]:
    try:
        res = call(token, f"/crm/v4/objects/{obj}/{oid}/associations/{to}",
                   None, "GET")
    except RuntimeError:
        return []
    return [str(r.get("toObjectId")) for r in res.get("results", [])]


def main() -> int:
    token = os.environ.get("QBS_HUBSPOT_TOKEN", "")
    if not token:
        print("set QBS_HUBSPOT_TOKEN", file=sys.stderr)
        return 1

    partner_domains, partner_by_domain = set(), {}
    for r in csv.DictReader(open(PARTNERS, encoding="utf-8-sig")):
        if r["domain"]:
            partner_domains.add(r["domain"])
            partner_by_domain[r["domain"]] = r

    found: dict[tuple[str, str], dict] = {}
    for obj, (text_props, extra) in OBJECTS.items():
        props = text_props + extra
        for prop in text_props:
            for kw in KEYWORDS:
                for h in search_keyword(token, obj, prop, kw, props):
                    key = (obj, h["id"])
                    if key not in found:
                        found[key] = {"object": obj, "id": h["id"],
                                      "props": h.get("properties", {}),
                                      "keywords": set()}
                    found[key]["keywords"].add(kw)
        print(f"  {obj}: {sum(1 for k in found if k[0]==obj)} matching records")

    print(f"\ntotal engagement records mentioning acquisition language: {len(found)}")
    if not found:
        return 0

    owners = {}
    try:
        for o in call(token, "/crm/v3/owners", None, "GET").get("results", []):
            owners[str(o["id"])] = (
                f"{o.get('firstName','')} {o.get('lastName','')}".strip()
                or o.get("email", ""))
    except RuntimeError:
        pass

    rows = []
    for (obj, oid), rec in found.items():
        comp_ids = associated(token, obj, oid, "companies")
        cont_ids = associated(token, obj, oid, "contacts")
        comps = []
        if comp_ids:
            res = call(token, "/crm/v3/objects/companies/batch/read",
                       {"properties": ["name", "domain", "website",
                                       "hubspot_partner", "hubspot_partner_tier"],
                        "inputs": [{"id": c} for c in comp_ids[:20]]})
            comps = [r["properties"] for r in res.get("results", [])]
        conts = []
        if cont_ids:
            res = call(token, "/crm/v3/objects/contacts/batch/read",
                       {"properties": ["email", "firstname", "lastname",
                                       "jobtitle", "hubspot_partner_contact"],
                        "inputs": [{"id": c} for c in cont_ids[:20]]})
            conts = [r["properties"] for r in res.get("results", [])]

        doms = {registrable_domain(c.get("domain") or c.get("website") or "")
                for c in comps}
        doms |= {registrable_domain((c.get("email") or "").split("@")[-1])
                 for c in conts}
        doms.discard("")
        matched = sorted(doms & partner_domains)
        p = rec["props"]
        body = (p.get("hs_meeting_body") or p.get("hs_email_text")
                or p.get("hs_note_body") or p.get("hs_call_body") or "")
        rows.append({
            "is_partner": "YES" if matched else "no",
            "partner_domain": "; ".join(matched),
            "partner_tier": "; ".join(
                partner_by_domain[d]["tier"] or "untiered" for d in matched),
            "type": obj[:-1],
            "date": (p.get("hs_meeting_start_time") or p.get("hs_timestamp")
                     or "")[:10],
            "subject": (p.get("hs_meeting_title") or p.get("hs_email_subject")
                        or p.get("hs_call_title") or "")[:160],
            "company": "; ".join(c.get("name") or "" for c in comps)[:80],
            "contacts": "; ".join(
                f"{c.get('firstname','')} {c.get('lastname','')}".strip()
                + (f" <{c.get('email')}>" if c.get("email") else "")
                for c in conts)[:200],
            "owner": owners.get(str(p.get("hubspot_owner_id") or ""), ""),
            "matched_keywords": "; ".join(sorted(rec["keywords"])),
            "excerpt": " ".join(body.split())[:400],
            "record_id": oid,
        })
        time.sleep(0.1)

    rows.sort(key=lambda r: (r["is_partner"] != "YES", r["date"]), reverse=False)
    rows.sort(key=lambda r: (r["is_partner"] != "YES", r["date"] or "0"))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    partner_rows = [r for r in rows if r["is_partner"] == "YES"]
    print(f"wrote {OUT} ({len(rows)} rows)")
    print(f"  involving a directory partner: {len(partner_rows)}")
    print("\n--- acquisition conversations WITH partners ---")
    for r in partner_rows:
        print(f"  {r['date']}  {r['type']:8s} {r['partner_domain']:28s} "
              f"[{r['partner_tier']}]  {r['subject'][:60]}")
        if r["contacts"]:
            print(f"      contacts: {r['contacts'][:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
