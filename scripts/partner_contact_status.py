#!/usr/bin/env python3
"""Report live coverage of the partner contact master list.

Answers the only question that matters for outreach: for how many partner
agencies do we hold a person, and for how many do we hold someone who could
actually make a decision?

Counts come from HubSpot, not from the CSVs in data/ - those are snapshots and
drift as soon as anything is loaded.

Read-only.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/partner_contact_status.py
"""

from __future__ import annotations

import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hubspot_api import HubSpotError, batched, call, search_all  # noqa: E402
from source_ma_decision_makers import is_decision_maker  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS = os.path.join(REPO, "data", "hubspot_partners.csv")

TIER_ORDER = ["Elite", "Diamond", "Platinum", "Gold", "Untiered"]


def flagged(prop: str) -> list[dict]:
    body = {
        "filterGroups": [{"filters": [
            {"propertyName": prop, "operator": "IN", "values": ["true"]}]}],
        "properties": ["email", "firstname", "lastname", "jobtitle",
                       "linkedin_profile_url__unique_value", "ma_target",
                       "ma_target_role", "ma_target_source",
                       "hubspot_partner_contact", "hubspot_partner_contact_tier"],
    }
    return search_all("contacts", body)


def company_of(contact_ids: list[str]) -> dict[str, str]:
    """contact id -> first associated company id, in batches."""
    out: dict[str, str] = {}
    for chunk in batched(contact_ids, 100):
        try:
            res = call("/crm/v4/associations/contacts/companies/batch/read",
                       {"inputs": [{"id": c} for c in chunk]})
        except HubSpotError as exc:
            print(f"  ! association batch: {exc}", file=sys.stderr)
            continue
        for r in res.get("results", []):
            to = r.get("to") or []
            if to:
                out[str(r["from"]["id"])] = str(to[0]["toObjectId"])
    return out


def main() -> int:
    partners = [p for p in csv.DictReader(open(PARTNERS, encoding="utf-8-sig"))]
    by_domain = {p["domain"]: p for p in partners if p["domain"]}
    dpg = {d for d, p in by_domain.items()
           if p["tier"] in ("diamond", "platinum", "gold")}
    top = {d for d, p in by_domain.items()
           if p["tier"] in ("elite", "diamond", "platinum", "gold")}

    contacts: dict[str, dict] = {}
    for prop in ("hubspot_partner_contact", "ma_target"):
        rows = flagged(prop)
        print(f"contacts flagged {prop:26s} {len(rows)}")
        for r in rows:
            contacts[r["id"]] = r["properties"]
    print(f"distinct partner-linked contacts            {len(contacts)}")

    # Resolve each contact to its company, then to a partner domain.
    comp = company_of(list(contacts))
    ids = sorted(set(comp.values()))
    dom_of: dict[str, str] = {}
    for chunk in batched(ids, 100):
        res = call("/crm/v3/objects/companies/batch/read",
                   {"properties": ["domain", "hubspot_partner_tier"],
                    "inputs": [{"id": c} for c in chunk]})
        for r in res.get("results", []):
            dom_of[r["id"]] = (r["properties"].get("domain") or "").lower()

    per_domain: dict[str, list[dict]] = collections.defaultdict(list)
    unlinked = 0
    for cid, props in contacts.items():
        d = dom_of.get(comp.get(cid, ""), "")
        if not d:
            unlinked += 1
            continue
        per_domain[d].append(props)

    covered = {d for d in per_domain if d in by_domain}
    dm_domains = {d for d, people in per_domain.items()
                  if d in by_domain and any(
                      is_decision_maker(p.get("jobtitle") or "")
                      or p.get("ma_target") == "true" for p in people)}

    print(f"  contacts with no company association      {unlinked}")
    print(f"\npartner agencies in the directory export    {len(by_domain)}")
    print(f"  with at least one contact                 {len(covered)}")
    print(f"  with a decision-maker                     {len(dm_domains)}")

    print("\ncoverage by tier (agency has a decision-maker):")
    for tier in TIER_ORDER:
        key = "" if tier == "Untiered" else tier.lower()
        tot = {d for d, p in by_domain.items() if p["tier"] == key}
        if not tot:
            continue
        anyc = len(tot & covered)
        dms = len(tot & dm_domains)
        print(f"  {tier:9s} {dms:>5} / {len(tot):>5} have a DM "
              f"({dms * 100 // len(tot):>2}%)   any contact: {anyc}")

    gap_dpg = len(dpg - dm_domains)
    print(f"\nDiamond/Platinum/Gold still with no decision-maker  {gap_dpg}")
    print(f"Elite+D/P/G still with no decision-maker            {len(top - dm_domains)}")

    src = collections.Counter(
        p.get("ma_target_source") or "-" for p in contacts.values()
        if p.get("ma_target") == "true")
    print(f"\nM&A targets by source: {dict(src)}")
    both = sum(1 for p in contacts.values()
               if p.get("ma_target") == "true"
               and p.get("hubspot_partner_contact") == "true")
    print(f"M&A targets also on the cold-outreach suppression list: {both}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
