#!/usr/bin/env python3
"""Assemble every M&A decision-maker we can actually reach into one load file.

Combines the two sourcing routes, which turn out not to overlap at all:

  A. data/acquisition_decision_makers.csv - 83 ZoomInfo-enriched owners at US
     Elite/Diamond partners, every one with a verified business email.
  B. data/partner_owners_found.csv - owners scraped from the partners' own team
     pages, reachable by LinkedIn URL and/or by a personal email found on the
     same site.

For B, an email is only used when its local part actually contains the person's
name (nikhil.jani@ for Nikhil Jani). Generic mailboxes are dropped: loading
hello@agency.com as a named contact's address creates a record that emails a
shared inbox while claiming to be the founder.

Phone numbers flagged Do Not Call by ZoomInfo are dropped rather than loaded -
once a number is in the CRM it will get dialled.

Output is data/ma_decision_makers.csv, the input to
load_ma_contacts_to_hubspot.py.

Usage:
    python3 scripts/build_ma_load_file.py
"""

from __future__ import annotations

import csv
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(REPO, "data")
ZI = os.path.join(D, "acquisition_decision_makers.csv")
SCRAPED = os.path.join(D, "partner_owners_found.csv")
OUT = os.path.join(D, "ma_decision_makers.csv")

COLUMNS = ["first_name", "last_name", "email", "linkedin_url", "job_title",
           "role", "company_domain", "partner_company", "tier", "country",
           "phone", "mobile_phone", "source", "accuracy", "valid_date",
           "zi_person_id"]

# Shared inboxes. A named contact must never carry one of these as their email.
GENERIC = re.compile(
    r"^(info|hello|hi|contact|sales|support|admin|office|team|marketing|"
    r"enquiries|inquiries|mail|hey|welcome|help|privacy|legal|jobs|careers|"
    r"noreply|no-reply|press|billing|accounts|finance|hr|newsletter|study|"
    r"partner|partners|service|services|kontakt|bonjour|hola)@", re.I)


def personal_email(name: str, mails: list[str]) -> str:
    """A site email that demonstrably belongs to this person, else ''."""
    parts = [p.lower() for p in name.split() if len(p) > 1]
    if len(parts) < 2:
        return ""
    first, last = parts[0], parts[-1]
    fallback = ""
    for e in mails:
        if GENERIC.match(e):
            continue
        bare = re.sub(r"[^a-z]", "", e.split("@")[0].lower())
        if (first in bare and last in bare) or bare == first + last:
            return e  # firstname.lastname - unambiguous
        if not fallback and bare in (first, last, first[0] + last,
                                     first + last[0]):
            fallback = e
    return fallback


def load(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def main() -> None:
    rows: list[dict] = []

    for r in load(ZI):
        if not r.get("email"):
            continue
        rows.append({
            "first_name": r["first_name"], "last_name": r["last_name"],
            "email": r["email"], "linkedin_url": "",
            "job_title": r.get("title", ""), "role": r.get("authority", ""),
            "company_domain": r["domain"],
            "partner_company": r.get("company", ""),
            "tier": (r.get("tier") or "").title(), "country": "US",
            # A number ZoomInfo marks Do Not Call does not go into the CRM.
            "phone": "" if r.get("direct_phone_dnc") == "Y" else r.get("direct_phone", ""),
            "mobile_phone": "" if r.get("mobile_phone_dnc") == "Y" else r.get("mobile_phone", ""),
            "source": "ZoomInfo", "accuracy": r.get("zi_accuracy", ""),
            "valid_date": r.get("zi_last_validated", "")[:10],
            "zi_person_id": r.get("zi_person_id", ""),
        })
    print(f"A. ZoomInfo enriched with email      {len(rows)}")

    before = len(rows)
    for r in load(SCRAPED):
        name = (r.get("owner_name") or "").strip()
        mails = [e.strip().lower() for e in (r.get("site_emails") or "").split(";")
                 if e.strip()]
        email = personal_email(name, mails)
        li = (r.get("owner_linkedin_url") or "").strip()
        if not email and not li:
            continue  # unreachable, so not worth a CRM record
        bits = name.split()
        rows.append({
            "first_name": bits[0], "last_name": " ".join(bits[1:]),
            "email": email, "linkedin_url": li,
            "job_title": (r.get("owner_title") or "").replace("/", " / "),
            "role": "", "company_domain": r["domain"],
            "partner_company": r.get("company_name", ""),
            "tier": (r.get("tier") or "").title(),
            "country": r.get("country", ""),
            "phone": "", "mobile_phone": "",
            "source": "Website" + (" + LinkedIn" if li else ""),
            # Scraped names carry no verified accuracy score; leaving this blank
            # keeps them visibly distinct from the ZoomInfo rows in HubSpot.
            "accuracy": "", "valid_date": "", "zi_person_id": "",
        })
    print(f"B. scraped owners reachable          {len(rows) - before}")

    # Owner/founder first, then rows carrying an email, then stronger tiers:
    # this is the order a human would work the list in.
    rank = {"Elite": 0, "Diamond": 1, "Platinum": 2, "Gold": 3}
    rows.sort(key=lambda r: (rank.get(r["tier"], 9), not r["email"],
                             r["partner_company"]))
    with open(OUT, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {OUT}: {len(rows)} contacts")
    print(f"  with email            {sum(1 for r in rows if r['email'])}")
    print(f"  with LinkedIn URL     {sum(1 for r in rows if r['linkedin_url'])}")
    print(f"  with both             {sum(1 for r in rows if r['email'] and r['linkedin_url'])}")
    print(f"  distinct companies    {len({r['company_domain'] for r in rows})}")
    tiers: dict[str, int] = {}
    for r in rows:
        tiers[r["tier"] or "untiered"] = tiers.get(r["tier"] or "untiered", 0) + 1
    print("  by tier               " + ", ".join(
        f"{k}={v}" for k, v in sorted(tiers.items(), key=lambda kv: rank.get(kv[0], 9))))


if __name__ == "__main__":
    main()
