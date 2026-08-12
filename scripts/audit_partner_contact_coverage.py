#!/usr/bin/env python3
"""Find partner contacts the coverage report cannot see, and explain why.

partner_contact_status.py counts a contact only when it is associated to a
company whose domain matches a partner AND carries a decision-maker job title.
Both conditions can fail on a contact that is perfectly good, so that report is a
floor rather than a measurement:

  * the contact has no company association at all
  * the contact hangs off a duplicate company record that never got tagged
  * the company record has a blank domain, so it never matched a partner
  * jobtitle is empty even though the person is the founder

This pass ignores all of that and matches on email domain alone, which is
independent of associations, flags and titles. It also counts how many partner
domains have more than one company record, since duplicates are the mechanism
that would strand last year's contacts on an untagged twin.

Read-only.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/audit_partner_contact_coverage.py
"""

from __future__ import annotations

import collections
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from domainutil import registrable_domain  # noqa: E402
from hubspot_api import call  # noqa: E402
from source_ma_decision_makers import is_decision_maker  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS = os.path.join(REPO, "data", "hubspot_partners.csv")
SCRATCH = os.environ.get("SCRATCH", "/tmp")
CACHE = os.path.join(SCRATCH, "all_contacts.jsonl")
OUT = os.path.join(REPO, "data", "partner_contact_audit.csv")

PROPS = ["email", "firstname", "lastname", "jobtitle", "createdate",
         "hubspot_partner_contact", "ma_target", "hs_object_id",
         "associatedcompanyid", "lifecyclestage", "hs_lead_status"]


def page_all(obj: str, props: list[str], cache: str) -> list[dict]:
    """Page an object type to exhaustion, caching so a re-run is instant.

    The list endpoint is used rather than search because search stops at 10,000
    records however you page it.
    """
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        print(f"  loaded {len(rows)} {obj} from cache")
        return rows
    rows, after, q = [], None, "&".join(f"properties={p}" for p in props)
    with open(cache, "w", encoding="utf-8") as fh:
        while True:
            url = f"/crm/v3/objects/{obj}?limit=100&{q}"
            if after:
                url += f"&after={after}"
            page = call(url)
            batch = page.get("results", [])
            for r in batch:
                fh.write(json.dumps(r) + "\n")
            rows.extend(batch)
            after = page.get("paging", {}).get("next", {}).get("after")
            print(f"  {obj}: {len(rows)}", end="\r", flush=True)
            if not after:
                break
            time.sleep(0.06)
    print(f"  {obj}: {len(rows)} total")
    return rows


def main() -> int:
    partners = {p["domain"]: p for p in
                csv.DictReader(open(PARTNERS, encoding="utf-8-sig"))
                if p["domain"]}
    tiered = {d for d, p in partners.items()
              if p["tier"] in ("elite", "diamond", "platinum", "gold")}
    print(f"partner domains: {len(partners)} ({len(tiered)} tiered)\n")

    print("paging all contacts (email-domain match needs the whole set):")
    contacts = page_all("contacts", PROPS, CACHE)

    hits, rows = [], []
    for c in contacts:
        p = c.get("properties") or {}
        email = (p.get("email") or "").strip().lower()
        if "@" not in email:
            continue
        dom = registrable_domain(email.split("@")[-1])
        if dom not in partners:
            continue
        hits.append((dom, p))
        rows.append({
            "partner_domain": dom,
            "partner_company": partners[dom]["company_name"],
            "tier": partners[dom]["tier"] or "untiered",
            "contact_id": c["id"],
            "name": f"{p.get('firstname','')} {p.get('lastname','')}".strip(),
            "email": email,
            "jobtitle": p.get("jobtitle") or "",
            "is_decision_maker": "YES" if is_decision_maker(p.get("jobtitle") or "") else "",
            "flagged_partner_contact": p.get("hubspot_partner_contact") or "",
            "flagged_ma_target": p.get("ma_target") or "",
            "has_company_association": "YES" if p.get("associatedcompanyid") else "",
            "created": (p.get("createdate") or "")[:10],
        })

    dom_any = {d for d, _ in hits}
    dom_dm = {d for d, p in hits if is_decision_maker(p.get("jobtitle") or "")}
    print(f"\ncontacts whose EMAIL DOMAIN is a partner domain: {len(hits)}")
    print(f"  distinct partner agencies represented          {len(dom_any)}")
    print(f"  agencies with a decision-maker-titled contact   {len(dom_dm)}")

    unflagged = [r for r in rows if r["flagged_partner_contact"] != "true"
                 and r["flagged_ma_target"] != "true"]
    print(f"\n  of those contacts, NOT flagged by either property {len(unflagged)}")
    print(f"    ...on {len({r['partner_domain'] for r in unflagged})} agencies")
    no_assoc = [r for r in rows if not r["has_company_association"]]
    print(f"  with no company association at all               {len(no_assoc)}")
    no_title = [r for r in rows if not r["jobtitle"]]
    print(f"  with a blank job title                           {len(no_title)}")

    by_year = collections.Counter(r["created"][:4] for r in rows)
    print("\n  when these contacts were created:")
    for y, n in sorted(by_year.items()):
        print(f"    {y}: {n}")

    print("\n  decision-maker coverage by tier, email-domain basis:")
    for tier in ("elite", "diamond", "platinum", "gold"):
        tot = {d for d, p in partners.items() if p["tier"] == tier}
        print(f"    {tier:9s} any contact {len(tot & dom_any):>4} / {len(tot):<5}"
              f"  decision-maker {len(tot & dom_dm):>4}")

    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
