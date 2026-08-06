#!/usr/bin/env python3
"""Create dynamic HubSpot company lists over the hubspot_partner_* properties.

Dynamic (not static) on purpose: membership re-evaluates as the monthly refresh
changes tiers, so a partner promoted to Elite moves lists on its own.

The "All" list is the one to reference as an exclusion in cold-outreach
sequences and workflows - that is what keeps partners out of prospecting.

Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/create_partner_lists.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.hubapi.com"
COMPANY = "0-2"


def prop_filter(prop: str, operation: dict) -> dict:
    return {"filterType": "PROPERTY", "property": prop, "operation": operation}


def bool_true(prop: str) -> dict:
    """A booleancheckbox is an enumeration in HubSpot, so filter it as one.

    Using operationType BOOL here returns 400: "property with type enumeration
    cannot be used with property operation type: BOOL".
    """
    return prop_filter(prop, {
        "operationType": "ENUMERATION", "operator": "IS_ANY_OF",
        "values": ["true"], "includeObjectsWithNoValueSet": False,
    })


def enum_any(prop: str, values: list[str]) -> dict:
    return prop_filter(prop, {
        "operationType": "ENUMERATION", "operator": "IS_ANY_OF",
        "values": values, "includeObjectsWithNoValueSet": False,
    })


# Enumeration filters reject IS_KNOWN, so "holds any accreditation" has to be
# expressed as IS_ANY_OF across every accreditation value.
ACCREDITATIONS = [
    "Onboarding", "Custom Integration", "CRM Implementation", "Data Migration",
    "Solutions Architecture Design", "Platform Enablement", "Content Experience",
    "Service Implementation", "HubSpot Customer Training",
]


def enum_known(prop: str) -> dict:
    return prop_filter(prop, {
        "operationType": "ENUMERATION", "operator": "IS_ANY_OF",
        "values": ACCREDITATIONS, "includeObjectsWithNoValueSet": False,
    })


def string_is(prop: str, value: str) -> dict:
    return prop_filter(prop, {
        "operationType": "STRING", "operator": "IS_EQUAL_TO",
        "value": value, "includeObjectsWithNoValueSet": False,
    })


def branch(filters: list[dict]) -> dict:
    """All filters ANDed together, wrapped in the OR/AND envelope the API wants."""
    return {
        "filterBranchType": "OR",
        "filterBranches": [{
            "filterBranchType": "AND",
            "filterBranches": [],
            "filters": filters,
        }],
        "filters": [],
    }


IS_PARTNER = bool_true("hubspot_partner")
TIERS = ["Elite", "Diamond", "Platinum", "Gold"]

LISTS = [
    ("HubSpot Partners - All",
     branch([IS_PARTNER])),
    ("HubSpot Partners - Tiered (Elite to Gold)",
     branch([IS_PARTNER, enum_any("hubspot_partner_tier", TIERS)])),
    ("HubSpot Partners - Elite",
     branch([IS_PARTNER, enum_any("hubspot_partner_tier", ["Elite"])])),
    ("HubSpot Partners - Diamond",
     branch([IS_PARTNER, enum_any("hubspot_partner_tier", ["Diamond"])])),
    ("HubSpot Partners - Platinum",
     branch([IS_PARTNER, enum_any("hubspot_partner_tier", ["Platinum"])])),
    ("HubSpot Partners - Gold",
     branch([IS_PARTNER, enum_any("hubspot_partner_tier", ["Gold"])])),
    ("HubSpot Partners - Untiered",
     branch([IS_PARTNER, enum_any("hubspot_partner_tier", ["Untiered"])])),
    ("HubSpot Partners - US",
     branch([IS_PARTNER, string_is("hubspot_partner_country", "US")])),
    ("HubSpot Partners - US Tiered",
     branch([IS_PARTNER, string_is("hubspot_partner_country", "US"),
             enum_any("hubspot_partner_tier", TIERS)])),
    ("HubSpot Partners - UK",
     branch([IS_PARTNER, string_is("hubspot_partner_country", "GB")])),
    ("HubSpot Partners - Accredited",
     branch([IS_PARTNER, enum_known("hubspot_partner_accreditations")])),
    ("HubSpot Partners - Solutions Partners only (not Providers)",
     branch([IS_PARTNER, enum_any("hubspot_partner_type", ["Partner"])])),
]


def post(token: str, path: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{API}{path}", data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"message": raw[:300]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("QBS_HUBSPOT_TOKEN", ""))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.token:
        print("set QBS_HUBSPOT_TOKEN", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps({"name": LISTS[1][0], "objectTypeId": COMPANY,
                          "processingType": "DYNAMIC",
                          "filterBranch": LISTS[1][1]}, indent=1))
        return 0

    made = failed = 0
    for name, fb in LISTS:
        code, body = post(args.token, "/crm/v3/lists", {
            "name": name,
            "objectTypeId": COMPANY,
            "processingType": "DYNAMIC",
            "filterBranch": fb,
        })
        if code in (200, 201):
            lst = body.get("list", body)
            print(f"  created  {name:52s} listId={lst.get('listId')}")
            made += 1
        else:
            print(f"  FAILED   {name:52s} HTTP {code} "
                  f"{str(body.get('message'))[:150]}", file=sys.stderr)
            failed += 1
        time.sleep(0.4)

    print(f"\ncreated {made} | failed {failed}")
    print("Membership counts populate asynchronously; give it a few minutes.")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
