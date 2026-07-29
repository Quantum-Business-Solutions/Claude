#!/usr/bin/env python3
"""Map CEO Juice / e-automate properties onto a HubSpot portal, and say what to build.

Answers three questions for a given portal, per property:

  map    a HubSpot property already exists with a matching name
  build  nothing matched — a property has to be created
  skip   a foreign key, an audit column, or a field null on every sampled record

Run it against any portal to get that portal's build list. This is the repeatable
half of the mapping work: the CEO Juice side comes from field_reference.py, the
HubSpot side is read live, and the verdicts are computed rather than maintained by
hand.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/field_reference.py --json docs/field-reference.json   # CJ side
    python scripts/hubspot_mapping.py --json docs/mapping.json           # verdicts

WHY NAME MATCHING AND NOT A HAND-MAINTAINED TABLE. Company alone carries 561
properties in the demo portal, 289 of them custom. A hand-written mapping table
against a moving target of that size is wrong within a week, and wrong in the
direction that creates duplicate properties. Matching is imperfect but it is
recomputable, and `build` is honestly reported as "no match found" rather than as
"no equivalent exists".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

HUBSPOT_API = "https://api.hubapi.com"

# CEO Juice object -> HubSpot object type. Standard objects cost nothing against a
# portal's custom-object budget, which is why the map prefers them.
TARGETS: dict[str, str | None] = {
    "Customer": "companies",
    "Contact": "contacts",
    "SalesOrder": "deals",
    "ServiceCall": "tickets",
    "Item": "products",
    "PrintReleafUsageRecord": "companies",
    # Custom objects: pass --object-map to point these at a portal's own type ids.
    "Equipment": None,
    "ModelMeters": None,
    "Contract": None,
    "ContractDetail": None,
    "Invoice": None,
    "InvoiceDetail": None,
    "SOOrderDetail": None,
}

# Verified unique in the sandbox data and safe to carry hasUniqueValue in HubSpot.
# serialNumber is deliberately ABSENT: 35 duplicated values and 8 blanks across 600
# equipment records, so marking it unique fails the sync on the first collision or
# silently merges two machines. It is still worth storing, just not as identity.
UNIQUE_KEYS = {
    "Customer": "customerNumber",
    # equipmentNumber, NOT serialNumber -- this is a deliberate deviation from
    # docs/reference/ceojuice-hubspot-properties.json in the QuoteCommand repo, which
    # sets hasUniqueValue on ea_serial_number. Its reasoning is good (a serial is what
    # a tech, a manufacturer and a lease schedule all agree on) but the data does not
    # support it: across 600 sandbox equipment records serialNumber has 35 DUPLICATED
    # values and 8 blanks, while equipmentNumber is 600/600 distinct with none blank.
    # A unique-value property with duplicate source data does not degrade -- HubSpot
    # rejects the second record outright, so Equipment sync dies on the first
    # collision or silently merges two machines into one.
    # Store serialNumber, absolutely. Just do not make it the identity.
    "Equipment": "equipmentNumber",
    "Contract": "contractNumber",
    "SalesOrder": "soNumber",
    "ServiceCall": "callNumber",
}

# Property naming follows the generated spec in the QuoteCommand repo:
#   ea_<snake_case_field>
# The ea_ prefix is load-bearing, not cosmetic: name, phone, city, address and
# description already exist on company, and a create against an existing internal
# name fails, aborting provisioning half-built. Both that spec and the auto-mapper's
# catalog are generated from the same vendored Swagger, so inventing names here would
# make the mapper fall back to token guessing -- and that failure is invisible, since
# the mapping screen keeps working and just stops suggesting.
HUBSPOT_PREFIX = "ea_"


def hubspot_name(cj_field: str) -> str:
    """The property name the generated spec uses for a CEO Juice field.

    DELIBERATELY NOT norm(). `norm` collapses synonyms (number->num, description->desc)
    because that widens MATCHING, which is what it exists for. Generating a name is the
    opposite job: it has to reproduce the spec exactly. Routing this through norm gave
    `ea_equipment_num` where the spec says `ea_equipment_number` — a one-token
    divergence that creates a duplicate property and stops the auto-mapper suggesting,
    without anything visibly failing.
    """
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", str(cj_field)).lower()
    return HUBSPOT_PREFIX + re.sub(r"[^a-z0-9]+", "_", s).strip("_")

# ---------------------------------------------------------------------------
# FIELD ROLES. Four different things wear an `Id` suffix in e-automate, and a sync
# that treats them alike gets all four wrong.
#
#   match_key    The business key a sync matches on. Carries hasUniqueValue in
#                HubSpot. Verified unique against real data — see MATCH_KEYS.
#   primary_key  e-automate's own surrogate PK. Kept as an immutable anchor for
#                tie-breaking, never as the match key: the number is what every
#                other system and every human actually references.
#   association  A foreign key pointing at another ENTITY we also sync.
#                THIS IS THE ONE THAT MATTERS. `customerId` on Equipment is not a
#                property — it is the Equipment→Company relationship. Written as an
#                integer column it is a dead number a rep cannot click, and the
#                association HubSpot exists to model never gets made.
#   lookup       A foreign key pointing at a CODE TABLE (terms, ship methods,
#                priorities). Resolvable to a label through a domain route, so it
#                should sync as the label, not the id. `termId: 1` means nothing on
#                a deal record; "Net 10" means something.
#   unresolvable A foreign key whose lookup route answers 403 for every key this API
#                issues — /api/User/* and /api/Branch. Skipped, and the reason is
#                reported rather than silently dropped, because it is a claim request
#                waiting to be made, not a modelling decision.
#   data         An ordinary value.
# ---------------------------------------------------------------------------

# Verified unique against live data before being trusted as a match key.
# ServiceCall.callNumber: 226 records, 0 blank, 0 duplicates.
# Equipment: equipmentNumber 600/600 distinct; serialNumber has 35 duplicated values
# and 8 blanks, which is why it is NOT here despite being the intuitive choice.
MATCH_KEYS = {
    "Customer": "customerNumber",
    "Equipment": "equipmentNumber",
    "Contract": "contractNumber",
    "SalesOrder": "soNumber",
    "ServiceCall": "callNumber",
    "Invoice": "invoiceNumber",
    "Item": "itemNumber",
}

PRIMARY_KEYS = {
    "customerId", "equipmentId", "contractId", "soId", "callId", "invoiceId",
    "itemId", "contactId", "modelMeterId",
}

# Entity foreign key -> the object it should ASSOCIATE to.
ASSOCIATIONS = {
    "customerId": "Customer", "billtoId": "Customer", "billToId": "Customer",
    "ovgBillToId": "Customer", "locationId": "Customer", "parentId": "Equipment",
    "contractId": "Contract", "contractLeaseId": "Contract", "leaseId": "Contract",
    "itemId": "Item", "modelId": "Item", "equipmentId": "Equipment",
    "quoteId": "SalesOrder", "origInvoiceId": "Invoice", "soId": "SalesOrder",
    "contactId": "Contact", "equipmentContactId": "Contact",
    "decisionContactId": "Contact", "meterContactId": "Contact",
    "orderedByContactId": "Contact",
}

# Code-table foreign key -> the lookup name get_list() resolves (all of these answer;
# the /api/ListsAndCodes/* family does not, so the domain routes are used).
LOOKUPS = {
    "termId": "Terms", "ovgBillToTermId": "Terms",
    "shipMethodId": "ShipMethods", "orderTypeId": "OrderTypes",
    "statusId": "OrderStatuses", "contractStatusId": "OrderStatuses",
    "priorityId": "Priorities", "slaCodeId": "SLACodes",
    "onHoldCodeId": "OnHoldCodes", "priceLevelId": "PriceLevels",
    "meterTypeId": "MeterTypes", "callTypeId": "CallTypes",
    "problemCodeId": "ProblemCodes", "repairCodeId": "RepairCodes",
    "cancelCodeId": "CancelCodes", "noteTypeId": "NoteTypes",
    "modelCategoryId": "ModelCategories", "makeId": "Makes",
}

# Lookup route is 403 for every key this API issues, so the id cannot be resolved to
# anything a human reads. Worth requesting the claims for.
UNRESOLVABLE = {
    "technicianId": "/api/User/Technicians (403)",
    "salesRepId": "/api/User/SalesReps (403)",
    "altSalesRepNumber": "/api/User/SalesReps (403)",
    "branchId": "/api/Branch (403)",
    "soBranchNumber": "/api/Branch (403)",
    "creatorId": "audit user (/api/User/Users 403)",
    "updatorId": "audit user (/api/User/Users 403)",
    "approvedById": "/api/User/Users (403)",
    "onHoldReleaserId": "/api/User/Users (403)",
}

AUDIT = {"lastupdate", "createdate", "notecount"}


def field_role(obj: str, name: str) -> tuple[str, str | None]:
    """(role, target) for one field. See the role table above."""
    if MATCH_KEYS.get(obj) == name:
        return "match_key", None
    if name in UNRESOLVABLE:
        return "unresolvable", UNRESOLVABLE[name]
    if name in LOOKUPS:
        return "lookup", LOOKUPS[name]
    # An object's own PK is an anchor; the same name on another object is a relationship.
    if name in PRIMARY_KEYS and norm(name).removesuffix("_id") == norm(obj):
        return "primary_key", None
    if name in ASSOCIATIONS:
        return "association", ASSOCIATIONS[name]
    if name.lower() in AUDIT:
        return "data", None
    if re.search(r"(Id|GUID)$", name):
        # An unrecognised *Id is still a pointer. Flagged rather than mapped, because
        # syncing an integer nobody can resolve is worse than leaving it out.
        return "unresolvable", "unclassified foreign key"
    return "data", None

# Applied to both sides before comparing, so bwVolume and bw_volume match.
SYNONYMS = [
    ("number", "num"), ("identifier", "id"), ("description", "desc"),
    ("address", "addr"), ("telephone", "phone"), ("quantity", "qty"),
    ("percent", "pct"), ("amount", "amt"),
]


def norm(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", str(name)).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    for a, b in SYNONYMS:
        s = s.replace(a, b)
    return s


def hubspot_properties(object_type: str, token: str) -> dict[str, tuple[str, str, bool]]:
    """{normalised name: (real name, type, hasUniqueValue)} for one object type."""
    req = urllib.request.Request(
        f"{HUBSPOT_API}/crm/v3/properties/{object_type}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            rows = json.loads(resp.read()).get("results", [])
    except urllib.error.HTTPError as exc:
        print(f"  ! {object_type}: HTTP {exc.code}", file=sys.stderr)
        return {}
    return {
        norm(r["name"]): (r["name"], r.get("type", ""), bool(r.get("hasUniqueValue")))
        for r in rows
    }


def classify(field: dict, obj: str, sampled: int, pool: dict) -> tuple[str, str | None]:
    name = field["field"]
    low = name.lower()
    role, _ = field_role(obj, name)

    if low in AUDIT:
        return "skip", None
    # A relationship, a resolvable code and a dead integer each need their own
    # treatment, and none of them is "create a property and copy the number".
    if role == "association":
        return "associate", None
    if role == "lookup":
        return "lookup", None
    if role == "unresolvable":
        return "skip", None
    if field["type"] not in ("string", "int", "decimal", "boolean", "datetime"):
        return "skip", None  # nested object or array
    # The match key must exist even where sampling is thin — it is the identity.
    if role == "match_key":
        key = norm(name)
        hit = pool.get(key)
        return ("map", hit[0]) if hit else ("build", None)

    # EMPTY BEATS MATCHED, and the order matters. Checking the name first reported
    # Contact as nine mappable properties: the names line up with HubSpot's contact
    # fields, but every one of them is null on all 137 sampled records, because the
    # API returns a join row with the nested contact object unhydrated. A field with
    # no data is not a mapping however well its name matches -- calling it one
    # produces a build plan that looks like progress and syncs nothing.
    if sampled and (field.get("fill_pct") or 0) == 0:
        return "skip", None

    key = norm(name)
    hit = pool.get(key)
    if not hit and len(pool) > 100:
        # Large pools often prefix or suffix: ea_customer_number vs customer_number.
        cands = [v for k, v in pool.items() if k.endswith("_" + key) or key.endswith("_" + k)]
        hit = cands[0] if len(cands) == 1 else None
    if hit:
        return "map", hit[0]

    return "build", None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--field-reference", type=Path, default=Path("docs/field-reference.json"))
    ap.add_argument("--json", type=Path, help="write the verdicts here")
    ap.add_argument(
        "--object-map",
        type=Path,
        help='JSON {"Equipment": "2-50535052", ...} pointing custom objects at this portal',
    )
    args = ap.parse_args()

    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        print("Set HUBSPOT_TOKEN (a private-app token for the target portal).", file=sys.stderr)
        return 2

    cj = json.loads(args.field_reference.read_text())
    targets = dict(TARGETS)
    if args.object_map:
        targets.update(json.loads(args.object_map.read_text()))

    pools: dict[str, dict] = {}
    for target in {t for t in targets.values() if t}:
        pools[target] = hubspot_properties(target, token)
        print(f"  {target}: {len(pools[target])} properties", file=sys.stderr)

    report = {}
    print(f"\n{'CJ object':<24}{'target':<16}{'props':>6}{'map':>5}{'build':>7}"
          f"{'assoc':>7}{'lookup':>7}{'skip':>6}")
    totals = [0, 0, 0, 0]
    for obj, target in targets.items():
        if obj not in cj:
            continue
        info = cj[obj]
        pool = pools.get(target or "", {})
        rows = []
        for f in info["fields"]:
            verdict, match = classify(f, obj, info["sampled"], pool)
            role, role_target = field_role(obj, f["field"])
            rows.append({
                "field": f["field"], "type": f["type"], "fill": f.get("fill_pct"),
                "verdict": verdict, "hubspot": match,
                "role": role, "roleTarget": role_target,
                "propose": hubspot_name(f["field"]) if verdict == "build" else match,
                "unique": MATCH_KEYS.get(obj) == f["field"],
            })
        counts = {v: sum(1 for r in rows if r["verdict"] == v)
                  for v in ("map", "build", "skip", "associate", "lookup")}
        report[obj] = {"target": target, "sampled": info["sampled"], "rows": rows,
                       "counts": counts, "matchKey": MATCH_KEYS.get(obj),
                       "matchKeyProperty": hubspot_name(MATCH_KEYS[obj]) if obj in MATCH_KEYS else None}
        print(f"{obj:<24}{str(target or '(none)'):<16}{len(rows):>6}"
              f"{counts['map']:>5}{counts['build']:>7}{counts['associate']:>7}"
              f"{counts['lookup']:>7}{counts['skip']:>6}")
        totals = [totals[0] + len(rows), totals[1] + counts["map"],
                  totals[2] + counts["build"], totals[3] + counts["skip"]]
    print("-" * 64)
    print(f"{'TOTAL':<40}{totals[0]:>6}{totals[1]:>5}{totals[2]:>7}{totals[3]:>6}")

    print("\nMATCH KEYS — create these with hasUniqueValue: true")
    for obj, key in MATCH_KEYS.items():
        print(f"  {obj:<16}{key:<20}-> {hubspot_name(key)}")
    print("  (serialNumber excluded on purpose — 35 duplicates / 8 blanks in 600 records)")

    if args.json:
        args.json.write_text(json.dumps(report, indent=1))
        print(f"\nwrote {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
