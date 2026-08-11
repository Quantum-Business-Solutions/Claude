#!/usr/bin/env python3
"""Create the HubSpot lists needed to actually run M&A outreach.

Split by how each person is reachable, because the two need different plays: an
email list can go into a sequence, a LinkedIn-only list has to be worked by hand
or through a LinkedIn tool.

The important one is the suppression-safe list. hubspot_partner_contact = true is
the cold-outreach exclusion list, and 34 of the M&A targets carry it because they
genuinely do work at a partner agency. That flag is factually correct and must
not be stripped. The fix belongs in the outreach audience instead: exclude
partner contacts EXCEPT where ma_target is true.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/create_ma_target_lists.py            # preview
    python3 scripts/create_ma_target_lists.py --commit
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hubspot_api import HubSpotError, call  # noqa: E402


def prop(name: str, operation: dict) -> dict:
    return {"filterType": "PROPERTY", "property": name, "operation": operation}


def is_true(name: str) -> dict:
    """A booleancheckbox is an enumeration in HubSpot; BOOL returns 400."""
    return prop(name, {"operationType": "ENUMERATION", "operator": "IS_ANY_OF",
                       "values": ["true"], "includeObjectsWithNoValueSet": False})


def known(name: str) -> dict:
    """"Has any value" - only ALL_PROPERTY accepts IS_KNOWN without a value.

    STRING + IS_KNOWN is rejected as "required fields were not set: [value]",
    and there is no working IS_NOT_KNOWN here at all, so the lists below are
    framed as "reachable by X" rather than "missing Y".
    """
    return prop(name, {"operationType": "ALL_PROPERTY", "operator": "IS_KNOWN"})


def any_of(name: str, values: list[str]) -> dict:
    return prop(name, {"operationType": "ENUMERATION", "operator": "IS_ANY_OF",
                       "values": values, "includeObjectsWithNoValueSet": False})


def branch(filters: list[dict]) -> dict:
    """AND across filters, wrapped in the OR envelope the API expects."""
    return {"filterBranchType": "OR", "filterBranches": [
        {"filterBranchType": "AND", "filterBranchOperator": "AND",
         "filters": filters, "filterBranches": []}],
        "filterBranchOperator": "OR", "filters": []}


LISTS = [
    ("M&A Targets - All", [is_true("ma_target")],
     "Every sourced owner/CEO/founder at an acquisition-target partner agency."),
    ("M&A Targets - Email Outreach", [is_true("ma_target"), known("email")],
     "M&A targets with a verified email - can go into a sequence."),
    # "LinkedIn reachable" rather than "no email": there is no usable
    # IS_NOT_KNOWN operator, and the ~10 people with both belong in both plays
    # anyway.
    ("M&A Targets - LinkedIn Reachable",
     [is_true("ma_target"), known("linkedin_profile_url__unique_value")],
     "M&A targets with a LinkedIn profile URL - work these by hand or via LinkedIn."),
    ("M&A Targets - Elite & Diamond", [is_true("ma_target"),
                                       any_of("ma_target_tier", ["Elite", "Diamond"])],
     "Highest-tier acquisition targets - work these first."),
    ("M&A Targets - Equity Holders", [is_true("ma_target"),
                                      any_of("ma_target_role",
                                             ["Owner", "Founder", "Co-Founder",
                                              "Chairman", "Managing Partner"])],
     "Owners and founders rather than hired executives - they can sell."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    args = ap.parse_args()

    existing = {}
    try:
        page = call("/crm/v3/lists/search", {"query": "M&A Targets", "count": 100})
        for lst in page.get("lists", []):
            existing[lst["name"]] = lst["listId"]
    except HubSpotError as exc:
        print(f"could not search existing lists: {exc}", file=sys.stderr)

    for name, filters, why in LISTS:
        if name in existing:
            print(f"exists  {name}  (listId {existing[name]})")
            continue
        if not args.commit:
            print(f"WOULD CREATE  {name}\n              {why}")
            continue
        try:
            res = call("/crm/v3/lists", {
                "name": name, "objectTypeId": "0-1", "processingType": "DYNAMIC",
                "filterBranch": branch(filters)})
            lst = res.get("list", res)
            print(f"created {name}  listId {lst.get('listId')}  "
                  f"size {lst.get('size', '?')}")
        except HubSpotError as exc:
            print(f"FAILED  {name}: {exc}", file=sys.stderr)

    if not args.commit:
        print("\nDRY RUN - pass --commit to create.")
        return 0
    print("\nReminder: any cold-outreach audience that excludes "
          "hubspot_partner_contact = true must add 'OR ma_target = true' as an "
          "exception, or 34 of these targets stay suppressed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
