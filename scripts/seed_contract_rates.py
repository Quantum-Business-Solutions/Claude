#!/usr/bin/env python3
"""Map e-automate's contracted rate fields, and populate them on the demo contracts.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/seed_contract_rates.py --apply

THE FIELDS EXIST. I SAID THEY DID NOT, AND I WAS WRONG.

I searched the field reference for "overage", found only billing DATES, and concluded
e-automate publishes no service or overage rate. It publishes several, on Contract:

    cppRate              decimal   cost per page
    cppServiceRate       decimal   THE SERVICE RATE
    cppHardwareAmount    decimal
    cppMinimumPages      int
    coveredCopies        int       the allowance
    accumCopies          decimal   copies accumulated to date
    expCopiesBase        int
    bsaMinimumBilling    decimal

Measured across 300 live contracts: every one of those fields is PRESENT in the payload and
every rate field is zero. expCopies is non-zero on 5 of 300; coveredCopies and accumCopies
on none. baseRate is populated on 231, so the object is not empty in general -- the rates
specifically are not filled in this sandbox.

AND THE RATE PROBABLY LIVES SOMEWHERE THE API DOES NOT EXPOSE. ovgRateScheduleStartDate is
populated on 248 of 300 contracts, and baseRateScheduleStartDate similarly. So e-automate
holds overage rates in a rate SCHEDULE entity, the contract points at one, and the API
returns the pointer's start date with no route to the schedule. Structurally the same
problem as the lease entity: contractLeaseId points at a lease no route returns.

WHAT THIS SCRIPT DOES ABOUT IT. Creates the HubSpot properties and the mapping rows so a
production dealer with populated rates gets them synced and displayed as CONTRACTED. Then
fills them on the DEMO- contracts only, derived from the same per-page rates the seeded
invoices use, so the two reconcile: the contracted rate the screen shows and the effective
rate it computes from invoices land on the same number instead of quietly disagreeing.

The account overview prefers the contracted rate when present and falls back to the
invoice-derived effective rate, labelling which it used -- the same pattern as volume, where
PrintReleaf is preferred and meters are the fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"
TOKEN = os.environ.get("HUBSPOT_TOKEN") or sys.exit("HUBSPOT_TOKEN not set")

CONTRACT = "2-36237359"
GROUP = "e_automate"
PREFIX = "DEMO-"

# The same rates the invoice fixture bills at, so contracted and effective agree.
RATE_BW, RATE_CLR = 0.0089, 0.0641
OVER_BW, OVER_CLR = 0.0121, 0.0795

PROPS = [
    ("ea_cpp_service_rate", "e-auto CPP Service Rate", "number", "number",
     "e-automate cppServiceRate. The contracted service rate per page. Zero on every "
     "contract in the CEO Juice sandbox, so the account review falls back to a rate "
     "derived from invoices and says which it used."),
    ("ea_cpp_rate", "e-auto CPP Rate", "number", "number",
     "e-automate cppRate — contracted cost per page."),
    ("ea_cpp_hardware_amount", "e-auto CPP Hardware Amount", "number", "number", None),
    ("ea_cpp_minimum_pages", "e-auto CPP Minimum Pages", "number", "number", None),
    ("ea_covered_copies", "e-auto Covered Copies", "number", "number",
     "The contracted allowance. Preferred over expCopies where both exist; empty on every "
     "sandbox contract."),
    ("ea_accum_copies", "e-auto Accumulated Copies", "number", "number",
     "Copies accumulated against the allowance to date. Where the running overage position "
     "would come from if e-automate filled it in."),
    ("ea_overage_rate_bw", "e-auto Overage Rate Mono", "number", "number",
     "Rate per mono page above allowance. NOT an e-automate field: the overage rate lives "
     "in a rate schedule entity that no API route exposes, so this is populated for the "
     "demo fixture and stays empty for real dealers."),
    ("ea_overage_rate_color", "e-auto Overage Rate Colour", "number", "number",
     "As above, for colour pages."),
    ("ea_ovg_rate_schedule_start", "e-auto Overage Rate Schedule Start",
     "date", "date",
     "e-automate ovgRateScheduleStartDate, populated on 248 of 300 sandbox contracts. "
     "Evidence that a rate schedule exists; the schedule itself has no route."),
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
        r = call("GET", f"/crm/v3/objects/{urllib.parse.quote(obj)}?" + urllib.parse.urlencode(q))
        if "__error" in r:
            sys.exit(f"read {obj}: {r['__error']} {r.get('__body','')}")
        yield from r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after:
            return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("properties ...", file=sys.stderr)
    have = {p["name"] for p in call("GET", f"/crm/v3/properties/{CONTRACT}").get("results", [])}
    for name, label, typ, field, desc in PROPS:
        if name in have:
            print(f"  {name}: exists", file=sys.stderr)
            continue
        if not args.apply:
            print(f"  {name}: WOULD CREATE", file=sys.stderr)
            continue
        body = {"name": name, "label": label, "type": typ, "fieldType": field,
                "groupName": GROUP}
        if desc:
            body["description"] = desc
        r = call("POST", f"/crm/v3/properties/{CONTRACT}", body)
        ok = "created" if "__error" not in r or r.get("__error") == 409 else \
            f"FAILED {r['__error']} {r.get('__body','')[:140]}"
        print(f"  {name}: {ok}", file=sys.stderr)

    if not args.apply:
        print("\n--plan only.", file=sys.stderr)
        return

    # Demo contracts, with the allowance we already wrote, so the contracted service rate
    # reconciles with what the invoices bill.
    demo = [c for c in page(CONTRACT, ["ea_contract_number", "ea_exp_copies", "base_rate"])
            if str((c.get("properties") or {}).get("ea_contract_number") or "")
            .startswith(PREFIX)]
    print(f"\n{len(demo)} demo contracts", file=sys.stderr)

    updates = []
    for c in demo:
        p = c["properties"]
        allow = float(p.get("ea_exp_copies") or 0)
        base = float(p.get("base_rate") or 0)
        if not allow:
            continue
        # The blended contracted rate implied by base rate over the allowance, which is
        # what a dealer would actually have written on the agreement.
        blended = base / allow if allow else 0
        updates.append({"id": c["id"], "properties": {
            "ea_cpp_service_rate": f"{blended:.5f}",
            "ea_cpp_rate": f"{blended:.5f}",
            "ea_covered_copies": str(int(allow)),
            # Accumulated: roughly a year at the allowance, so a running position exists.
            "ea_accum_copies": str(int(allow * 11.4)),
            "ea_cpp_minimum_pages": str(int(allow * 0.5)),
            "ea_overage_rate_bw": f"{OVER_BW:.4f}",
            "ea_overage_rate_color": f"{OVER_CLR:.4f}",
        }})

    done = 0
    for i in range(0, len(updates), 100):
        r = call("POST", f"/crm/v3/objects/{CONTRACT}/batch/update",
                 {"inputs": updates[i:i + 100]})
        if "__error" in r:
            print(f"  ! {r['__error']} {r.get('__body','')[:300]}", file=sys.stderr)
            continue
        done += len(r.get("results", []))
    print(f"contracted rates written to {done}/{len(updates)} demo contracts", file=sys.stderr)

    print("\nVERIFY (direct read, not search — the index lags a batch write)", file=sys.stderr)
    for c in demo[:6]:
        r = call("GET", f"/crm/v3/objects/{CONTRACT}/{c['id']}"
                        f"?properties=ea_contract_number,ea_cpp_service_rate,"
                        f"ea_covered_copies,ea_overage_rate_bw,ea_overage_rate_color,"
                        f"ea_accum_copies")
        p = r.get("properties") or {}
        print(f"  {str(p.get('ea_contract_number')):16} service {p.get('ea_cpp_service_rate')}"
              f"  covered {p.get('ea_covered_copies')}  accum {p.get('ea_accum_copies')}"
              f"  ovg mono {p.get('ea_overage_rate_bw')} colour {p.get('ea_overage_rate_color')}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
