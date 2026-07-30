#!/usr/bin/env python3
"""Give every device a per-machine monthly volume by apportioning its customer's REAL total.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/allocate_device_volume.py --plan
    python scripts/allocate_device_volume.py --apply

WHY THIS IS NOT MAKING NUMBERS UP.

Measured: 0 of 120 meters in this portal carry a non-zero value on ANY volume field, and
CEO Juice returns the same zeros through /api/MeterReadings/EquipmentMetersByEqNo. There
is no per-machine reading to sync. What DOES exist is a measured customer total from
/api/PrintReleaf/customers/{id} — 143,964 pages a month for HSBC, 2.9M lifetime for Bank
of America — already rolled onto each Company as ea_fleet_monthly_volume.

A rep argues a replacement device by device: this machine does 2,000 pages against a
50,000 duty cycle, that one is over its rating and has had six calls. With no per-machine
figure the fleet table cannot support that conversation at all. So the customer's measured
total is divided across their devices and written to a SEPARATE property,
ea_allocated_monthly_volume, which the account overview reads only when the machine has no
meter reading, and reports with basis `allocated`.

The honesty is in the labelling and in the separate property. The total is real; the split
between machines is not, and the UI says so on every figure. Writing this into
ea_avg_monthly_volume12_mo instead would have been the same arithmetic and a lie, because
that field means "e-automate computed this from readings".

THE SPLIT IS EQUAL, DELIBERATELY. Weighting by anything available here — install date,
model, meter count — would imply a relationship the data does not support and would be
harder to explain than "the customer's total over their machine count". An equal split is
obviously an apportionment at a glance, which is the point.
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
GROUP = "e_automate"

PROPS = [
    ("ea_allocated_monthly_volume", "e-auto Allocated Monthly Volume", "number", "number",
     "The customer's MEASURED monthly total (PrintReleaf) divided equally across their "
     "devices. An apportionment, not a meter reading: the fleet figure it sums to was "
     "counted, the split between machines was not. Read only where the machine has no "
     "meter reading, and always shown as 'Allocated'."),
    ("ea_allocated_color_pct", "e-auto Allocated Colour Share %", "number", "number",
     "The customer's colour share applied to this device. Same caveat as the allocated "
     "volume: the customer figure is measured, the per-device attribution is not."),
]


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


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def ensure_props(apply: bool) -> None:
    have = {p["name"] for p in call("GET", f"/crm/v3/properties/{EQUIPMENT}").get("results", [])}
    for name, label, typ, field, desc in PROPS:
        if name in have:
            print(f"  {name}: exists", file=sys.stderr)
            continue
        if not apply:
            print(f"  {name}: WOULD CREATE", file=sys.stderr)
            continue
        r = call("POST", f"/crm/v3/properties/{EQUIPMENT}",
                 {"name": name, "label": label, "type": typ, "fieldType": field,
                  "groupName": GROUP, "description": desc})
        ok = "created" if "__error" not in r or r.get("__error") == 409 else \
            f"FAILED {r['__error']} {r.get('__body','')[:140]}"
        print(f"  {name}: {ok}", file=sys.stderr)


def assoc_batch(frm: str, to: str, ids: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in range(0, len(ids), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/read",
                 {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        for res in (r.get("results") or []):
            out[res["from"]["id"]] = [str(t["toObjectId"]) for t in res.get("to", [])]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("properties:", file=sys.stderr)
    ensure_props(args.apply)

    print("\nreading portal ...", file=sys.stderr)
    companies = [c for c in page(COMPANY, ["name", "ea_customer_number",
                                           "ea_fleet_monthly_volume",
                                           "ea_fleet_volume_basis",
                                           "ea_fleet_color_pct"])
                 if num((c.get("properties") or {}).get("ea_fleet_monthly_volume"))]
    print(f"  {len(companies)} companies carry a measured monthly volume", file=sys.stderr)

    cids = [c["id"] for c in companies]
    co_to_eq = assoc_batch(COMPANY, EQUIPMENT, cids)

    updates: list[tuple[str, dict]] = []
    preview = []
    skipped_no_dev = 0
    for c in companies:
        p = c["properties"]
        total = num(p.get("ea_fleet_monthly_volume")) or 0
        colour = num(p.get("ea_fleet_color_pct"))
        devs = co_to_eq.get(c["id"], [])
        if not devs or total <= 0:
            skipped_no_dev += 1
            continue
        per = total / len(devs)
        for d in devs:
            props = {"ea_allocated_monthly_volume": str(int(round(per)))}
            if colour is not None:
                props["ea_allocated_color_pct"] = str(colour)
            updates.append((d, props))
        preview.append((total, p.get("name"), len(devs), int(round(per)),
                        p.get("ea_fleet_volume_basis")))

    preview.sort(reverse=True)
    print(f"\n{'company':32} {'total/mo':>10} {'devices':>8} {'each/mo':>9}  basis",
          file=sys.stderr)
    for t, n, d, per, b in preview[:14]:
        print(f"{str(n)[:32]:32} {t:10,.0f} {d:8} {per:9,}  {b}", file=sys.stderr)
    print(f"\n  {len(updates)} device rows to write across {len(preview)} companies; "
          f"{skipped_no_dev} companies have a volume but no associated device",
          file=sys.stderr)

    if not args.apply:
        print("\n--plan only. Re-run with --apply.", file=sys.stderr)
        return

    done = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i:i + 100]
        r = call("POST", f"/crm/v3/objects/{EQUIPMENT}/batch/update",
                 {"inputs": [{"id": d, "properties": pr} for d, pr in chunk]})
        if "__error" in r:
            print(f"  ! batch {i//100}: {r['__error']} {r.get('__body','')[:200]}",
                  file=sys.stderr)
            continue
        done += len(r.get("results", []))
    print(f"\n{done}/{len(updates)} devices updated", file=sys.stderr)

    # Read the destination back rather than trusting the batch status.
    v = call("POST", f"/crm/v3/objects/{EQUIPMENT}/search",
             {"limit": 1, "properties": ["hs_object_id"],
              "filterGroups": [{"filters": [
                  {"propertyName": "ea_allocated_monthly_volume",
                   "operator": "GT", "value": "0"}]}]})
    print(f"VERIFY ea_allocated_monthly_volume > 0 on {v.get('total')} devices",
          file=sys.stderr)


if __name__ == "__main__":
    main()
