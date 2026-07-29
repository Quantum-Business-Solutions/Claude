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
    """The property name the generated spec would use for a CEO Juice field."""
    return HUBSPOT_PREFIX + norm(cj_field)

# Foreign keys point at rows we often cannot even read -- /api/User/* and /api/Branch
# are 403 -- so they arrive as unresolvable integers. Primary keys are kept: they are
# the immutable anchor a sync can fall back to.
PRIMARY_KEYS = {
    "customerId", "equipmentId", "contractId", "soId", "callId", "invoiceId",
    "itemId", "contactId", "modelMeterId",
}
AUDIT = {"lastupdate", "createdate", "creatorid", "updatorid", "notecount"}

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

    # Foreign keys and audit columns are noise; primary keys are not.
    if low in AUDIT:
        return "skip", None
    if re.search(r"(id|guid)$", name) and name not in PRIMARY_KEYS:
        return "skip", None
    if field["type"] not in ("string", "int", "decimal", "boolean", "datetime"):
        return "skip", None  # nested object or array

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
    print(f"\n{'CJ object':<24}{'target':<16}{'props':>6}{'map':>5}{'build':>7}{'skip':>6}")
    totals = [0, 0, 0, 0]
    for obj, target in targets.items():
        if obj not in cj:
            continue
        info = cj[obj]
        pool = pools.get(target or "", {})
        rows = []
        for f in info["fields"]:
            verdict, match = classify(f, obj, info["sampled"], pool)
            rows.append({
                "field": f["field"], "type": f["type"], "fill": f.get("fill_pct"),
                "verdict": verdict, "hubspot": match,
                "unique": UNIQUE_KEYS.get(obj) == f["field"],
            })
        counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in ("map", "build", "skip")}
        report[obj] = {"target": target, "sampled": info["sampled"], "rows": rows,
                       "counts": counts, "uniqueKey": UNIQUE_KEYS.get(obj)}
        print(f"{obj:<24}{str(target or '(none)'):<16}{len(rows):>6}"
              f"{counts['map']:>5}{counts['build']:>7}{counts['skip']:>6}")
        totals = [totals[0] + len(rows), totals[1] + counts["map"],
                  totals[2] + counts["build"], totals[3] + counts["skip"]]
    print("-" * 64)
    print(f"{'TOTAL':<40}{totals[0]:>6}{totals[1]:>5}{totals[2]:>7}{totals[3]:>6}")

    print("\nUnique keys to create with hasUniqueValue: true")
    for obj, key in UNIQUE_KEYS.items():
        print(f"  {obj:<16}{key}")
    print("  (serialNumber excluded on purpose — 35 duplicates / 8 blanks in 600 records)")

    if args.json:
        args.json.write_text(json.dumps(report, indent=1))
        print(f"\nwrote {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
