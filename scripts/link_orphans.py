#!/usr/bin/env python3
"""Associate the records that were loaded but never wired to anything.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/link_orphans.py --plan     # show what would be linked
    python scripts/link_orphans.py --apply

WHY THIS IS NEEDED SEPARATELY FROM THE LOADER. The loader links a child to its parent
only when both are inside the slice it happens to be holding. Load meters for 200
machines and companies for 160 customers and the meters whose machine arrived in a
later batch never get an edge -- they are in the portal, correct, and invisible on
every record page, because a HubSpot record page shows ONLY associated records.
98 of 120 meters and 26 of 40 service calls were in that state.

This works entirely off properties already in the portal: every child carries
ea_equipment_number and ea_customer_number, so the edge can be rebuilt without going
back to CEO Juice. That also makes it safe to re-run after any future load.

Association type ids are DISCOVERED, never hardcoded -- they differ per portal, and a
wrong type id creates a real edge of the wrong kind, which is worse than no edge
because it looks fine on the record page.
"""

from __future__ import annotations

import argparse
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

COMPANY = "company"
EQUIPMENT = "2-50535052"
METER = "2-66645402"
SERVICE_CALL = "2-66645395"
CONTRACT = "2-36237359"


def call(method: str, path: str, body=None, tries: int = 5):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(f"{API}{path}", data=data, method=method)
        req.add_header("Authorization", f"Bearer {TOKEN}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            body_txt = e.read()[:400].decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": e.code, "__body": body_txt}
        except Exception as e:  # noqa: BLE001
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": "net", "__body": str(e)}
    return {"__error": "exhausted"}


def page(obj: str, props: list[str]):
    after = None
    while True:
        q = {"limit": 100, "properties": ",".join(props)}
        if after:
            q["after"] = after
        r = call("GET", f"/crm/v3/objects/{urllib.parse.quote(obj)}?"
                        + urllib.parse.urlencode(q))
        if "__error" in r:
            sys.exit(f"read {obj}: {r['__error']} {r.get('__body','')}")
        yield from r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after:
            return


def assoc_type(frm: str, to: str) -> int:
    """The portal's own id for the default (unlabelled) association of this pair."""
    r = call("GET", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                    f"{urllib.parse.quote(to)}/labels")
    if "__error" in r:
        sys.exit(f"discover {frm}->{to}: {r['__error']} {r.get('__body','')}")
    results = r.get("results", [])
    for t in results:
        if t.get("label") is None:          # the primary/unlabelled type
            return t["typeId"]
    if not results:
        sys.exit(f"no association type exists between {frm} and {to}")
    return results[0]["typeId"]


def existing(frm: str, to: str, ids: list[str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for i in range(0, len(ids), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/read",
                 {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        for res in (r.get("results") or []):
            out[res["from"]["id"]] = {str(t["toObjectId"]) for t in res.get("to", [])}
    return out


def create(frm: str, to: str, type_id: int, pairs: list[tuple[str, str]]) -> int:
    """v4 batch create, 100 per call. Already-existing edges are a no-op, not an error."""
    done = 0
    for i in range(0, len(pairs), 100):
        chunk = pairs[i:i + 100]
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/create",
                 {"inputs": [{"from": {"id": a}, "to": {"id": b},
                              "types": [{"associationCategory": "USER_DEFINED",
                                         "associationTypeId": type_id}]}
                             for a, b in chunk]})
        if "__error" in r:
            print(f"  ! batch {i//100}: {r['__error']} {r.get('__body','')}",
                  file=sys.stderr)
            continue
        done += len(r.get("results", []))
    return done


def index(records, prop) -> dict[str, str]:
    """value -> record id. Blanks skipped; a duplicate keeps the first, which is why
    the key properties were verified unique before any of this was trusted."""
    out = {}
    for r in records:
        v = (r.get("properties") or {}).get(prop)
        if v and str(v).strip() and str(v) not in out:
            out[str(v)] = r["id"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("reading portal...", file=sys.stderr)
    companies = list(page(COMPANY, ["ea_customer_number"]))
    equipment = list(page(EQUIPMENT, ["ea_equipment_number"]))
    meters = list(page(METER, ["ea_equipment_number", "ea_customer_number",
                               "ea_meter_type_code"]))
    calls = list(page(SERVICE_CALL, ["ea_equipment_number", "ea_customer_number"]))
    contracts = list(page(CONTRACT, ["ea_contract_number", "ea_customer_number"]))

    by_cust = index(companies, "ea_customer_number")
    by_equip = index(equipment, "ea_equipment_number")
    print(f"  {len(by_cust)} companies keyed, {len(by_equip)} machines keyed",
          file=sys.stderr)

    # (child records, child object id, label) -> parents to link
    plans: list[tuple[str, str, str, list[tuple[str, str]], list[str]]] = []

    def build(child_obj, child_recs, parent_obj, parent_idx, match_prop, label):
        have = existing(child_obj, parent_obj, [r["id"] for r in child_recs])
        pairs, unmatched = [], []
        for r in child_recs:
            v = (r.get("properties") or {}).get(match_prop)
            pid = parent_idx.get(str(v)) if v else None
            if not pid:
                unmatched.append(f"{r['id']}:{v}")
                continue
            if pid in have.get(r["id"], set()):
                continue                    # already wired
            pairs.append((r["id"], pid))
        plans.append((child_obj, parent_obj, label, pairs, unmatched))

    build(METER, meters, EQUIPMENT, by_equip, "ea_equipment_number", "Meter -> Equipment")
    build(METER, meters, COMPANY, by_cust, "ea_customer_number", "Meter -> Company")
    build(SERVICE_CALL, calls, EQUIPMENT, by_equip, "ea_equipment_number",
          "Service Call -> Equipment")
    build(SERVICE_CALL, calls, COMPANY, by_cust, "ea_customer_number",
          "Service Call -> Company")
    build(CONTRACT, contracts, COMPANY, by_cust, "ea_customer_number",
          "Contract -> Company")

    for child, parent, label, pairs, unmatched in plans:
        print(f"{label:30} {len(pairs):5} to create   "
              f"{len(unmatched):4} unmatched", file=sys.stderr)
        if unmatched[:3]:
            print(f"{'':30} e.g. {unmatched[:3]}", file=sys.stderr)

    if not args.apply:
        print("\n--plan only. Re-run with --apply.", file=sys.stderr)
        return

    total = 0
    for child, parent, label, pairs, _ in plans:
        if not pairs:
            continue
        tid = assoc_type(child, parent)
        n = create(child, parent, tid, pairs)
        total += n
        print(f"{label:30} linked {n}/{len(pairs)} (typeId {tid})", file=sys.stderr)
    print(f"\n{total} associations created", file=sys.stderr)


if __name__ == "__main__":
    main()
