#!/usr/bin/env python3
"""Wire Equipment -> Contract (and -> Lease) from ContractDetail lines.

    export HUBSPOT_TOKEN=pat-na1-... CEOJUICE_USERNAME=... CEOJUICE_PASSWORD=...
    python scripts/link_equipment_contracts.py --plan
    python scripts/link_equipment_contracts.py --apply [--all]

WHY THIS CANNOT BE DONE FROM THE EQUIPMENT SIDE. e-automate's Equipment record carries no
contractId at all. The ONLY edge between a machine and its contract is
ContractDetail.equipmentId, which is also why Lease had to become its own object rather
than columns on Contract. So the link has to be built by walking contracts and reading
their lines.

AND THE LINES ARE NOT ON THE LIST ROUTE. /api/Contract/... returns `details` as an empty
collection on every contract; only /api/Contract/ByContractNumber/{n} hydrates it. Same
shape as ServiceCall.equipment being null on AllOpen. That costs one request per contract,
which is why this is a separate script rather than part of the bulk loader.

WHY IT NEEDED RUNNING AGAIN. A previous pass linked 106 machines. A later reload took
Equipment from 199 to 1,259 records, and the new ones arrived with no contract edge — so
the count read 0 across every account and the joined fleet grid had an empty Contract
column, which is the one column that cannot be got from HubSpot natively. An association
is not a property: reloading the records does not recreate the edges.

Scope defaults to companies that actually have equipment, because the point is a usable
fleet view rather than a complete graph; --all walks every contract in the portal.
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
CONTRACT = "2-36237359"
LEASE = "2-50535055"


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
            txt = e.read()[:300].decode("utf-8", "replace")
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
        r = call("GET", f"/crm/v3/objects/{urllib.parse.quote(obj)}?" + urllib.parse.urlencode(q))
        if "__error" in r:
            sys.exit(f"read {obj}: {r['__error']} {r.get('__body','')}")
        yield from r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after:
            return


def assoc_type(frm: str, to: str) -> int | None:
    r = call("GET", f"/crm/v4/associations/{urllib.parse.quote(frm)}/{urllib.parse.quote(to)}/labels")
    if "__error" in r:
        print(f"  ! no association labels {frm}->{to}: {r['__error']}", file=sys.stderr)
        return None
    results = r.get("results", [])
    for t in results:
        if t.get("label") is None:
            return t["typeId"]
    return results[0]["typeId"] if results else None


def existing(frm: str, to: str, ids: list[str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for i in range(0, len(ids), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/read",
                 {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        for res in (r.get("results") or []):
            out[res["from"]["id"]] = {str(t["toObjectId"]) for t in res.get("to", [])}
    return out


def create(frm: str, to: str, pairs: list[tuple[str, str]], label: str) -> int:
    if not pairs:
        return 0
    tid = assoc_type(frm, to)
    if tid is None:
        print(f"  {label}: SKIPPED — no association definition exists", file=sys.stderr)
        return 0
    made = 0
    for i in range(0, len(pairs), 100):
        chunk = pairs[i:i + 100]
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/create",
                 {"inputs": [{"from": {"id": a}, "to": {"id": b},
                              "types": [{"associationCategory": "USER_DEFINED",
                                         "associationTypeId": tid}]} for a, b in chunk]})
        if "__error" in r:
            print(f"  ! {label} batch {i//100}: {r['__error']} {r.get('__body','')}", file=sys.stderr)
            continue
        made += len(r.get("results", []))
    print(f"  {label}: {made}/{len(pairs)} edges (typeId {tid})", file=sys.stderr)
    return made


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
    ap.add_argument("--all", action="store_true",
                    help="walk every contract, not only those on companies with equipment")
    args = ap.parse_args()

    print("reading portal ...", file=sys.stderr)
    equipment = list(page(EQUIPMENT, ["ea_equipment_number"]))
    contracts = list(page(CONTRACT, ["ea_contract_number", "contractnumber"]))
    leases = list(page(LEASE, ["ea_contract_detail_id", "ea_equipment_number",
                               "ea_contract_number"]))
    by_equip = index(equipment, "ea_equipment_number")
    # Contract number lives under either spelling depending on which load wrote it.
    by_contract: dict[str, str] = {}
    for r in contracts:
        p = r.get("properties") or {}
        for key in ("ea_contract_number", "contractnumber"):
            v = p.get(key)
            if v and str(v).strip() and str(v) not in by_contract:
                by_contract[str(v).strip()] = r["id"]
    print(f"  {len(by_equip)} machines keyed, {len(by_contract)} contract numbers keyed, "
          f"{len(leases)} leases", file=sys.stderr)

    # Which contracts to walk. Bounded by default: one detail request each.
    if args.all:
        want = sorted(by_contract)
    else:
        eq_ids = [r["id"] for r in equipment]
        eq_to_co = existing(EQUIPMENT, COMPANY, eq_ids)
        companies = {c for v in eq_to_co.values() for c in v}
        co_to_ct = existing(COMPANY, CONTRACT, sorted(companies))
        wanted_ids = {x for v in co_to_ct.values() for x in v}
        id_to_no = {}
        for r in contracts:
            p = r.get("properties") or {}
            no = p.get("ea_contract_number") or p.get("contractnumber")
            if no:
                id_to_no[r["id"]] = str(no).strip()
        want = sorted({id_to_no[i] for i in wanted_ids if i in id_to_no})
        print(f"  {len(companies)} companies have equipment; {len(want)} of their contracts "
              f"to hydrate", file=sys.stderr)

    cj = CeoJuiceClient()
    print(f"hydrating {len(want)} contracts via ByContractNumber ...", file=sys.stderr)

    # (equipmentNumber, contractNumber) pairs from the contract LINES.
    lines: list[tuple[str, str]] = []
    no_details = 0
    failed = 0
    for i, cn in enumerate(want, 1):
        try:
            d = cj.get(f"/api/Contract/ByContractNumber/{urllib.parse.quote(str(cn))}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            if failed <= 5:
                print(f"  ! {cn}: {e}", file=sys.stderr)
            continue
        if isinstance(d, list):
            d = d[0] if d else {}
        details = (d or {}).get("details") or []
        if not details:
            no_details += 1
            continue
        for ln in details:
            eqno = ln.get("equipmentNumber") or (ln.get("equipment") or {}).get("equipmentNumber")
            if eqno:
                lines.append((str(eqno).strip(), str(cn)))
        if i % 25 == 0:
            print(f"  {i}/{len(want)}  lines so far {len(lines)}", file=sys.stderr)

    print(f"  {len(lines)} contract lines carry an equipment number; "
          f"{no_details} contracts had no lines, {failed} fetch failures", file=sys.stderr)

    # Plan Equipment -> Contract.
    eq_ids_all = [r["id"] for r in equipment]
    have = existing(EQUIPMENT, CONTRACT, eq_ids_all)
    pairs, unmatched_eq, unmatched_ct = [], set(), set()
    seen = set()
    for eqno, cn in lines:
        e = by_equip.get(eqno)
        c = by_contract.get(cn)
        if not e:
            unmatched_eq.add(eqno)
            continue
        if not c:
            unmatched_ct.add(cn)
            continue
        if c in have.get(e, set()) or (e, c) in seen:
            continue
        seen.add((e, c))
        pairs.append((e, c))

    # Equipment -> Lease, from the Lease records themselves: they already carry both an
    # equipment number and a contract number, so no CEO Juice call is needed.
    ls_ids = [r["id"] for r in leases]
    have_ls = existing(EQUIPMENT, LEASE, ls_ids and eq_ids_all or [])
    ls_pairs = []
    for r in leases:
        p = r.get("properties") or {}
        e = by_equip.get(str(p.get("ea_equipment_number") or ""))
        if e and r["id"] not in have_ls.get(e, set()):
            ls_pairs.append((e, r["id"]))

    print("\nPLAN", file=sys.stderr)
    print(f"  Equipment -> Contract   {len(pairs)} new edges", file=sys.stderr)
    print(f"  Equipment -> Lease      {len(ls_pairs)} new edges", file=sys.stderr)
    if unmatched_eq:
        print(f"  {len(unmatched_eq)} equipment numbers on contract lines are not in the "
              f"portal: {sorted(unmatched_eq)[:8]}", file=sys.stderr)
    if unmatched_ct:
        print(f"  {len(unmatched_ct)} contract numbers could not be matched in the portal: "
              f"{sorted(unmatched_ct)[:8]}", file=sys.stderr)

    if not args.apply:
        print("\n--plan only. Re-run with --apply.", file=sys.stderr)
        return

    print("\nAPPLY", file=sys.stderr)
    create(EQUIPMENT, CONTRACT, pairs, "Equipment -> Contract")
    create(EQUIPMENT, LEASE, ls_pairs, "Equipment -> Lease")

    # Read the destination back. A 2xx on a batch endpoint is not proof.
    print("\nVERIFY", file=sys.stderr)
    for to, label in ((CONTRACT, "Equipment -> Contract"), (LEASE, "Equipment -> Lease")):
        e = existing(EQUIPMENT, to, eq_ids_all)
        print(f"  {label}: {sum(len(v) for v in e.values())} edges across "
              f"{sum(1 for v in e.values() if v)} machines", file=sys.stderr)


if __name__ == "__main__":
    main()
