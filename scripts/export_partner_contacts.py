#!/usr/bin/env python3
"""Export every contact associated with a HubSpot-partner company.

These are the records that actually matter for outreach suppression: a cold
sequence targets contacts, so flagging the company alone does not stop anything
unless the sequence filters on the associated company.

Read-only unless --tag is passed, which stamps hubspot_partner_contact on each
contact so contact-level lists and sequence filters can use a single property
instead of relying on association traversal.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/export_partner_contacts.py
    python3 scripts/export_partner_contacts.py --tag
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.hubapi.com"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(REPO_ROOT, "data", "partner_contacts.csv")
BATCH = 100


def call(token: str, path: str, payload: dict | None = None,
         method: str = "POST") -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(6):
        req = urllib.request.Request(
            f"{API}{path}", data=data, method=method,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()[:400]
            if exc.code == 429 or exc.code >= 500:
                time.sleep(min(2**attempt, 20))
                continue
            raise RuntimeError(f"HTTP {exc.code} {path}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"gave up on {path}")


def partner_company_ids(token: str) -> dict[str, dict]:
    """Every company flagged hubspot_partner, keyed by id."""
    out: dict[str, dict] = {}
    after = None
    while True:
        body = {
            "limit": 100,
            "filterGroups": [{"filters": [
                {"propertyName": "hubspot_partner", "operator": "EQ",
                 "value": "true"}]}],
            "properties": ["name", "domain", "hubspot_partner_tier",
                           "hubspot_partner_country", "hubspot_partner_type"],
        }
        if after:
            body["after"] = after
        page = call(token, "/crm/v3/objects/companies/search", body)
        for r in page.get("results", []):
            out[r["id"]] = r["properties"]
        after = page.get("paging", {}).get("next", {}).get("after")
        print(f"  partner companies: {len(out)}", end="\r", flush=True)
        if not after:
            break
        time.sleep(0.15)
    print(f"  partner companies: {len(out)}")
    return out


def contacts_for_companies(token: str, company_ids: list[str]) -> dict[str, set]:
    """company id -> set of associated contact ids."""
    assoc: dict[str, set] = {}
    for i in range(0, len(company_ids), BATCH):
        chunk = company_ids[i : i + BATCH]
        res = call(token, "/crm/v4/associations/companies/contacts/batch/read",
                   {"inputs": [{"id": c} for c in chunk]})
        for r in res.get("results", []):
            cid = r.get("from", {}).get("id")
            targets = {t.get("toObjectId") for t in r.get("to", [])}
            if cid and targets:
                assoc.setdefault(str(cid), set()).update(str(t) for t in targets)
        print(f"  associations read: {min(i+BATCH,len(company_ids))}"
              f"/{len(company_ids)}", end="\r", flush=True)
        time.sleep(0.15)
    print(f"  associations read: {len(company_ids)}/{len(company_ids)}")
    return assoc


def read_contacts(token: str, ids: list[str]) -> dict[str, dict]:
    props = ["email", "firstname", "lastname", "jobtitle", "company",
             "lifecyclestage", "hs_email_optout", "hubspot_owner_id",
             "createdate", "hs_lead_status"]
    out: dict[str, dict] = {}
    for i in range(0, len(ids), BATCH):
        chunk = ids[i : i + BATCH]
        res = call(token, "/crm/v3/objects/contacts/batch/read",
                   {"properties": props, "inputs": [{"id": c} for c in chunk]})
        for r in res.get("results", []):
            out[r["id"]] = r["properties"]
        print(f"  contacts read: {len(out)}/{len(ids)}", end="\r", flush=True)
        time.sleep(0.15)
    print(f"  contacts read: {len(out)}/{len(ids)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("QBS_HUBSPOT_TOKEN", ""))
    ap.add_argument("--tag", action="store_true",
                    help="stamp hubspot_partner_contact=true on each contact")
    args = ap.parse_args()
    if not args.token:
        print("set QBS_HUBSPOT_TOKEN", file=sys.stderr)
        return 1

    companies = partner_company_ids(args.token)
    assoc = contacts_for_companies(args.token, list(companies))

    contact_to_company: dict[str, str] = {}
    for comp_id, contact_ids in assoc.items():
        for c in contact_ids:
            # A contact on two partner companies keeps the stronger tier.
            prev = contact_to_company.get(c)
            rank = {"Elite": 0, "Diamond": 1, "Platinum": 2, "Gold": 3,
                    "Untiered": 4}
            if prev is None:
                contact_to_company[c] = comp_id
            else:
                a = rank.get(companies[comp_id].get("hubspot_partner_tier"), 5)
                b = rank.get(companies[prev].get("hubspot_partner_tier"), 5)
                if a < b:
                    contact_to_company[c] = comp_id

    print(f"\ncompanies with contacts: {len(assoc)}")
    print(f"unique partner contacts: {len(contact_to_company)}")
    if not contact_to_company:
        return 0

    details = read_contacts(args.token, list(contact_to_company))

    rows = []
    for cid, comp_id in contact_to_company.items():
        p = details.get(cid, {})
        comp = companies.get(comp_id, {})
        rows.append({
            "contact_id": cid,
            "email": p.get("email") or "",
            "first_name": p.get("firstname") or "",
            "last_name": p.get("lastname") or "",
            "job_title": p.get("jobtitle") or "",
            "lifecycle_stage": p.get("lifecyclestage") or "",
            "lead_status": p.get("hs_lead_status") or "",
            "email_optout": p.get("hs_email_optout") or "",
            "created": (p.get("createdate") or "")[:10],
            "partner_company": comp.get("name") or "",
            "partner_domain": comp.get("domain") or "",
            "partner_tier": comp.get("hubspot_partner_tier") or "",
            "partner_country": comp.get("hubspot_partner_country") or "",
            "partner_type": comp.get("hubspot_partner_type") or "",
            "company_id": comp_id,
        })

    rank = {"Elite": 0, "Diamond": 1, "Platinum": 2, "Gold": 3, "Untiered": 4}
    rows.sort(key=lambda r: (rank.get(r["partner_tier"], 5),
                             r["partner_company"].lower()))
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT_CSV} ({len(rows)} rows)")

    tiers: dict[str, int] = {}
    for r in rows:
        tiers[r["partner_tier"] or "(none)"] = tiers.get(
            r["partner_tier"] or "(none)", 0) + 1
    print("\ncontacts by partner tier:")
    for t in ("Elite", "Diamond", "Platinum", "Gold", "Untiered", "(none)"):
        if t in tiers:
            print(f"  {t:10s} {tiers[t]}")
    with_email = sum(1 for r in rows if r["email"])
    print(f"\nwith an email address: {with_email} of {len(rows)}")

    if args.tag:
        print("\ntagging contacts with hubspot_partner_contact=true")
        today = time.strftime("%Y-%m-%d")
        inputs = [
            {"id": r["contact_id"], "properties": {
                "hubspot_partner_contact": "true",
                "hubspot_partner_contact_tier": r["partner_tier"] or "Untiered",
                "hubspot_partner_contact_synced_on": today}}
            for r in rows
        ]
        ok = bad = 0
        for i in range(0, len(inputs), BATCH):
            chunk = inputs[i : i + BATCH]
            try:
                call(args.token, "/crm/v3/objects/contacts/batch/update",
                     {"inputs": chunk})
                ok += len(chunk)
            except RuntimeError as exc:
                bad += len(chunk)
                print(f"\n  ! batch {i}: {exc}", file=sys.stderr)
            print(f"  tagged {ok + bad}/{len(inputs)}", end="\r", flush=True)
            time.sleep(0.2)
        print(f"\ntagged {ok} | failed {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
