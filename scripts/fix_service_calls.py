#!/usr/bin/env python3
"""Backfill Service Call identity and wire the edges the loader could not.

    export HUBSPOT_TOKEN=pat-na1-... CEOJUICE_USERNAME=... CEOJUICE_PASSWORD=...
    python scripts/fix_service_calls.py --plan
    python scripts/fix_service_calls.py --apply

TWO API SHAPES CAUSED THIS, AND BOTH WILL BITE ANY OTHER SYNC.

1. ServiceCall carries `customerId` -- a surrogate -- and no customerNumber. So a call
   cannot be attached to a Company without first building customerId -> customerNumber
   from /api/Customer. The loader had no such map, so it wrote nothing, and
   ea_customer_number sat 0% filled on all 40 records in the portal.

2. `equipment` is NULL on /api/ServiceCall/AllOpen for all 226 calls, and a FULL nested
   Equipment object on /api/ServiceCall/ByCallNumber/{n}. Measured, not assumed. This is
   the same shape as Contract.details[]: list routes drop nested collections silently.
   A sync that reads only list routes concludes no call has equipment -- which reads as
   missing data rather than the wrong route, so nobody goes looking.

The cost of the fix is one detail request per call. That is why it is a separate script
rather than part of the bulk loader: hydrating 226 calls is 226 round trips, which is
fine occasionally and wrong on every incremental sync.

Meters are also repaired here. All 120 are reachable, but by two different paths -- 98
have a Company edge only, 22 an Equipment edge only, none have both. So a company record
lists meters that its own machines do not, which looks like data loss from either side.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ceojuice.client import CeoJuiceClient  # noqa: E402

API = "https://api.hubapi.com"
TOKEN = os.environ.get("HUBSPOT_TOKEN") or sys.exit("HUBSPOT_TOKEN not set")

COMPANY = "company"
EQUIPMENT = "2-50535052"
METER = "2-66645402"
SERVICE_CALL = "2-66645395"


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
            txt = e.read()[:400].decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": e.code, "__body": txt}
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
    r = call("GET", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                    f"{urllib.parse.quote(to)}/labels")
    if "__error" in r:
        sys.exit(f"discover {frm}->{to}: {r['__error']} {r.get('__body','')}")
    for t in r.get("results", []):
        if t.get("label") is None:
            return t["typeId"]
    results = r.get("results", [])
    if not results:
        sys.exit(f"no association type between {frm} and {to}")
    return results[0]["typeId"]


def read_edges(frm: str, to: str, ids: list[str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for i in range(0, len(ids), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/read",
                 {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        for res in (r.get("results") or []):
            out[res["from"]["id"]] = {str(t["toObjectId"]) for t in res.get("to", [])}
    return out


def make_edges(frm: str, to: str, pairs: list[tuple[str, str]], label: str) -> int:
    if not pairs:
        return 0
    tid = assoc_type(frm, to)
    made = 0
    for i in range(0, len(pairs), 100):
        chunk = pairs[i:i + 100]
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/create",
                 {"inputs": [{"from": {"id": a}, "to": {"id": b},
                              "types": [{"associationCategory": "USER_DEFINED",
                                         "associationTypeId": tid}]} for a, b in chunk]})
        if "__error" in r:
            print(f"  ! {label} batch {i//100}: {r['__error']} {r.get('__body','')}",
                  file=sys.stderr)
            continue
        made += len(r.get("results", []))
    print(f"  {label}: {made}/{len(pairs)} edges (typeId {tid})", file=sys.stderr)
    return made


def patch(obj: str, updates: list[tuple[str, dict]], label: str) -> int:
    """Batch update. 207 means PARTIAL failure and is not an error status -- read the
    per-row results rather than trusting the response code."""
    done = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i:i + 100]
        r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/batch/update",
                 {"inputs": [{"id": rid, "properties": props} for rid, props in chunk]})
        if "__error" in r:
            print(f"  ! {label} batch {i//100}: {r['__error']} {r.get('__body','')}",
                  file=sys.stderr)
            continue
        done += len(r.get("results", []))
        for e in (r.get("errors") or []):
            print(f"  ! {label}: {str(e)[:200]}", file=sys.stderr)
    print(f"  {label}: {done}/{len(updates)} records updated", file=sys.stderr)
    return done


def index(records, prop) -> dict[str, str]:
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

    cj = CeoJuiceClient()

    print("resolving customerId -> customerNumber from /api/Customer ...", file=sys.stderr)
    customers = list(cj.customers())
    cust_no = {r.get("customerId"): r.get("customerNumber") for r in customers}
    print(f"  {len(cust_no)} customers", file=sys.stderr)

    print("reading portal ...", file=sys.stderr)
    hs_calls = list(page(SERVICE_CALL, ["ea_call_number", "ea_customer_number",
                                        "ea_equipment_number"]))
    hs_companies = list(page(COMPANY, ["ea_customer_number"]))
    hs_equipment = list(page(EQUIPMENT, ["ea_equipment_number"]))
    hs_meters = list(page(METER, ["ea_equipment_number", "ea_customer_number"]))
    by_cust = index(hs_companies, "ea_customer_number")
    by_equip = index(hs_equipment, "ea_equipment_number")
    print(f"  {len(hs_calls)} calls, {len(by_cust)} keyed companies, "
          f"{len(by_equip)} keyed machines, {len(hs_meters)} meters", file=sys.stderr)

    # ── Hydrate each loaded call from the detail route ──────────────────────
    print(f"hydrating {len(hs_calls)} calls via ByCallNumber ...", file=sys.stderr)
    updates: list[tuple[str, dict]] = []
    call_equip: dict[str, str] = {}     # hubspot call id -> equipmentNumber
    call_cust: dict[str, str] = {}
    failed = 0
    for i, rec in enumerate(hs_calls, 1):
        cn = (rec.get("properties") or {}).get("ea_call_number")
        if not cn:
            continue
        try:
            d = cj.service_call(cn)
        except Exception as e:  # noqa: BLE001 - one bad call must not kill the run
            failed += 1
            print(f"  ! call {cn}: {e}", file=sys.stderr)
            continue
        if isinstance(d, list):
            d = d[0] if d else {}
        props: dict[str, str] = {}
        cnum = cust_no.get(d.get("customerId"))
        if cnum:
            props["ea_customer_number"] = str(cnum)
            call_cust[rec["id"]] = str(cnum)
        eq = d.get("equipment") or {}
        if eq.get("equipmentNumber"):
            props["ea_equipment_number"] = str(eq["equipmentNumber"])
            call_equip[rec["id"]] = str(eq["equipmentNumber"])
        if eq.get("serialNumber"):
            props["ea_serial_number"] = str(eq["serialNumber"])
        if props:
            updates.append((rec["id"], props))
        if i % 10 == 0:
            print(f"  {i}/{len(hs_calls)}", file=sys.stderr)

    print(f"  {len(updates)} calls have something to write, {failed} fetch failures",
          file=sys.stderr)
    print(f"  customer resolved: {len(call_cust)}  equipment resolved: {len(call_equip)}",
          file=sys.stderr)

    # ── Plan the edges ─────────────────────────────────────────────────────
    sc_ids = [r["id"] for r in hs_calls]
    have_sc_co = read_edges(SERVICE_CALL, COMPANY, sc_ids)
    have_sc_eq = read_edges(SERVICE_CALL, EQUIPMENT, sc_ids)

    sc_co = [(cid, by_cust[c]) for cid, c in call_cust.items()
             if c in by_cust and by_cust[c] not in have_sc_co.get(cid, set())]
    sc_eq = [(cid, by_equip[e]) for cid, e in call_equip.items()
             if e in by_equip and by_equip[e] not in have_sc_eq.get(cid, set())]

    # Meters: give every meter BOTH edges, not one or the other.
    m_ids = [r["id"] for r in hs_meters]
    have_m_co = read_edges(METER, COMPANY, m_ids)
    have_m_eq = read_edges(METER, EQUIPMENT, m_ids)
    m_co, m_eq = [], []
    for r in hs_meters:
        p = r.get("properties") or {}
        c, e = p.get("ea_customer_number"), p.get("ea_equipment_number")
        if c and str(c) in by_cust and by_cust[str(c)] not in have_m_co.get(r["id"], set()):
            m_co.append((r["id"], by_cust[str(c)]))
        if e and str(e) in by_equip and by_equip[str(e)] not in have_m_eq.get(r["id"], set()):
            m_eq.append((r["id"], by_equip[str(e)]))

    print("\nPLAN", file=sys.stderr)
    print(f"  patch  ServiceCall properties      {len(updates)}", file=sys.stderr)
    print(f"  link   ServiceCall -> Company      {len(sc_co)}", file=sys.stderr)
    print(f"  link   ServiceCall -> Equipment    {len(sc_eq)}", file=sys.stderr)
    print(f"  link   Meter -> Company            {len(m_co)}", file=sys.stderr)
    print(f"  link   Meter -> Equipment          {len(m_eq)}", file=sys.stderr)

    # Machines a call or meter points at that are not in the portal at all. Reported
    # rather than silently dropped: it is the difference between "nothing to link" and
    # "the parent was never loaded".
    absent = {e for e in call_equip.values() if e not in by_equip}
    absent |= {(r.get("properties") or {}).get("ea_equipment_number")
               for r in hs_meters
               if (r.get("properties") or {}).get("ea_equipment_number") not in by_equip}
    absent.discard(None)
    if absent:
        print(f"\n  {len(absent)} referenced machines are NOT in the portal, so those "
              f"edges cannot be made:\n    {sorted(absent)[:12]}", file=sys.stderr)

    if not args.apply:
        print("\n--plan only. Re-run with --apply.", file=sys.stderr)
        return

    print("\nAPPLY", file=sys.stderr)
    patch(SERVICE_CALL, updates, "ServiceCall properties")
    make_edges(SERVICE_CALL, COMPANY, sc_co, "ServiceCall -> Company")
    make_edges(SERVICE_CALL, EQUIPMENT, sc_eq, "ServiceCall -> Equipment")
    make_edges(METER, COMPANY, m_co, "Meter -> Company")
    make_edges(METER, EQUIPMENT, m_eq, "Meter -> Equipment")

    # Read the destination back. A 200 or a 207 proves nothing about what landed.
    print("\nVERIFY (read back from HubSpot)", file=sys.stderr)
    for prop in ("ea_customer_number", "ea_equipment_number"):
        r = call("POST", f"/crm/v3/objects/{SERVICE_CALL}/search",
                 {"limit": 1, "properties": ["hs_object_id"],
                  "filterGroups": [{"filters": [{"propertyName": prop,
                                                 "operator": "HAS_PROPERTY"}]}]})
        print(f"  ServiceCall.{prop}: {r.get('total')} filled", file=sys.stderr)
    for frm, to, label in ((SERVICE_CALL, COMPANY, "ServiceCall -> Company"),
                           (SERVICE_CALL, EQUIPMENT, "ServiceCall -> Equipment"),
                           (METER, COMPANY, "Meter -> Company"),
                           (METER, EQUIPMENT, "Meter -> Equipment")):
        ids = sc_ids if frm == SERVICE_CALL else m_ids
        e = read_edges(frm, to, ids)
        print(f"  {label}: {sum(len(v) for v in e.values())} edges across "
              f"{sum(1 for v in e.values() if v)} parents", file=sys.stderr)


if __name__ == "__main__":
    main()
