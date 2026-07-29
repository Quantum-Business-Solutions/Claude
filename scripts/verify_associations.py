#!/usr/bin/env python3
"""What is actually associated to what in the portal, and via which path.

Answers the question a record page cannot: for a given Company, how does HubSpot
know which Equipment, Contracts and Leases belong to it -- and is every record
reachable, or are some floating unassociated where nobody will ever see them.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/verify_associations.py

THE CHAIN MATTERS. e-automate does not give you Company->Equipment directly on
Equipment; there is no contractId on an Equipment record at all. The only edge
between a machine and its contract is ContractDetail.equipmentId, which is why Lease
sits where it does. An orphan count above zero means records were loaded but the
edge was never written, and those records are invisible on the record page even
though they exist.
"""

from __future__ import annotations

import collections
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"
TOKEN = os.environ.get("HUBSPOT_TOKEN") or sys.exit("HUBSPOT_TOKEN not set")


def call(method: str, path: str, body=None, tries: int = 4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(f"{API}{path}", data=data, method=method)
        req.add_header("Authorization", f"Bearer {TOKEN}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": e.code, "__body": e.read()[:400].decode("utf-8", "replace")}
        except Exception as e:  # noqa: BLE001
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": "net", "__body": str(e)}
    return {"__error": "exhausted"}


def page(obj: str, props: list[str], limit: int = 100):
    after = None
    while True:
        q = {"limit": limit, "properties": ",".join(props)}
        if after:
            q["after"] = after
        r = call("GET", f"/crm/v3/objects/{urllib.parse.quote(obj)}?"
                        + urllib.parse.urlencode(q))
        if "__error" in r:
            print(f"  ! {obj}: {r['__error']} {r.get('__body','')}", file=sys.stderr)
            return
        yield from r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after:
            return


def edges(frm: str, to: str, ids: list[str]) -> dict[str, list[str]]:
    """Batch-read associations. 100 ids per call, which is the documented cap."""
    out: dict[str, list[str]] = {}
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/read",
                 {"inputs": [{"id": x} for x in chunk]})
        if "__error" in r:
            print(f"  ! {frm}->{to}: {r['__error']} {r.get('__body','')}", file=sys.stderr)
            continue
        for res in r.get("results", []):
            out[res["from"]["id"]] = [t["toObjectId"] for t in res.get("to", [])]
    return out


OBJ = {
    "company":      ("company",      ["name", "ea_customer_number"]),
    "equipment":    ("2-50535052",   ["ea_equipment_number", "ea_serial_number"]),
    "contract":     ("2-36237359",   ["ea_contract_number", "ea_exp_date"]),
    "lease":        ("2-50535055",   ["ea_contract_detail_id", "ea_lease_schedule"]),
    "meter":        ("2-66645402",   ["ea_meter_type_code"]),
    "service_call": ("2-66645395",   ["ea_call_number"]),
    "invoice":      ("2-66645175",   ["ea_invoice_number"]),
}

# Every edge the record page depends on. If one is missing, the corresponding card
# on the company record is empty regardless of how many records were loaded.
LINKS = [
    ("company", "equipment"), ("company", "contract"), ("company", "lease"),
    ("company", "service_call"), ("company", "invoice"),
    ("equipment", "meter"), ("equipment", "contract"), ("equipment", "lease"),
    ("contract", "lease"),
]


def main() -> None:
    recs = {}
    for role, (oid, props) in OBJ.items():
        recs[role] = list(page(oid, props))
        print(f"{role:13} {len(recs[role]):5} records", file=sys.stderr)

    report = {"records": {k: len(v) for k, v in recs.items()}, "links": {}, "orphans": {}}

    linked_to: dict[str, set[str]] = collections.defaultdict(set)
    for frm, to in LINKS:
        ids = [r["id"] for r in recs[frm]]
        if not ids or not recs[to]:
            report["links"][f"{frm}->{to}"] = {"edges": 0, "from_with_any": 0,
                                               "note": "no records on one side"}
            continue
        e = edges(OBJ[frm][0], OBJ[to][0], ids)
        total = sum(len(v) for v in e.values())
        with_any = sum(1 for v in e.values() if v)
        report["links"][f"{frm}->{to}"] = {
            "edges": total,
            "from_with_any": with_any,
            "from_total": len(ids),
            "avg_per_parent": round(total / with_any, 1) if with_any else 0,
        }
        for v in e.values():
            linked_to[to].update(str(x) for x in v)
        print(f"{frm}->{to:13} {total:5} edges  "
              f"{with_any}/{len(ids)} parents linked", file=sys.stderr)

    # An orphan is a record nobody can reach from a Company. It exists in the portal
    # and is invisible on every record page.
    for role in ("equipment", "contract", "lease", "meter", "service_call", "invoice"):
        all_ids = {r["id"] for r in recs[role]}
        report["orphans"][role] = {
            "count": len(all_ids - linked_to[role]),
            "of": len(all_ids),
            "sample": sorted(all_ids - linked_to[role])[:5],
        }

    json.dump(report, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
