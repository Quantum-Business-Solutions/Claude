#!/usr/bin/env python3
"""Fill every writable e-automate field on the DEMO- records, so a fully-populated account
can be looked at rather than imagined.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/fill_demo_fields.py --plan
    python scripts/fill_demo_fields.py --apply

WHY. Real e-automate data is sparse in ways that make the review hard to judge: install
dates blank, locations blank, warranty blank, lease terms blank. Looking at it, you cannot
tell which columns are thin because the SCREEN is unfinished and which are thin because the
SOURCE is. Filling one account completely separates those two questions permanently.

RULES THAT KEEP THIS HONEST.

  1. DEMO- records only. Selected by key prefix, never by object sweep.
  2. Never overwrite. Only properties that are currently empty are touched, so every value
     deliberately set by the fixture or computed by a rollup survives untouched. This is the
     rule that makes the script safe to re-run and safe to run after any other seeding.
  3. Skip HubSpot-calculated and read-only properties. Writing those returns 400 for the
     whole batch, and a batch that fails wholesale on one bad field is how 1,220 identical
     errors happened earlier in this project.
  4. Values are plausible for the FIELD, derived from its name and type, not "x". A demo
     full of placeholder text teaches nothing about layout, column width or truncation --
     which is most of what looking at a filled-out account is for.

Enumeration properties take a real option from the property's own definition rather than a
guessed string, because an invalid option is another whole-batch 400.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"
TOKEN = os.environ.get("HUBSPOT_TOKEN") or sys.exit("HUBSPOT_TOKEN not set")

PREFIX = "DEMO-"
TODAY = dt.date(2026, 7, 30)

OBJECTS = [
    ("company", "ea_customer_number", "Company"),
    ("2-50535052", "ea_equipment_number", "Equipment"),
    ("2-36237359", "ea_contract_number", "Contract"),
    ("2-50535055", "ea_contract_detail_id", "Lease"),
    ("2-66645402", "ea_meter_key", "Meter"),
    ("2-66645395", "ea_call_number", "Service Call"),
    ("2-66645175", "ea_invoice_number", "Invoice"),
]

# Never touched. Keys and anything the fixture or a rollup owns: overwriting a computed
# volume with a plausible-looking invention is exactly the failure this project has been
# avoiding all along.
PROTECTED = {
    "ea_customer_number", "ea_equipment_number", "ea_contract_number", "contractnumber",
    "ea_contract_detail_id", "ea_meter_key", "ea_call_number", "ea_invoice_number",
    "ea_serial_number", "ea_avg_monthly_volume12_mo", "ea_avg_monthly_volume6_mo",
    "ea_avg_monthly_volume3_mo", "ea_avg_monthly_volume_install",
    "ea_mfg_suggested_monthly_volume", "ea_target_monthly_volume",
    "ea_meter_type_code", "ea_allocated_monthly_volume", "ea_allocated_color_pct",
    # Equipment-level volume rollups. Left out of this list on the first run, and the
    # generator duly filled them with numbers that CONTRADICTED the device's own meters:
    # DEMO-EQ-0101 got mono 59,000 and colour 33,000 against meters reading 18,400 and
    # 9,600, with a total of 1,430 that was smaller than either part. Plausible-looking
    # and internally impossible, which is the worst kind of demo data — it teaches a
    # reader that the screen is inconsistent when the screen was right.

    # Anything that RESTATES a figure held elsewhere belongs here. The rule is not "these
    # specific fields": it is that a generator must never author a value that another
    # record already determines.
    "ea_bw_avg_monthly_volume12_mo", "ea_color_avg_monthly_volume12_mo",
    "ea_total_avg_monthly_volume12_mo", "ea_meter_count", "ea_is_metered",
    "ea_most_recent_default_meter_reading_display",
    "ea_exp_copies", "ea_covered_copies", "base_rate", "ea_base_rate_period",
    "ea_invoice_amount", "ea_invoice_base_amount", "ea_invoice_overage_amount",
    "ea_cpp_service_rate", "ea_cpp_rate", "ea_overage_rate_bw", "ea_overage_rate_color",
    "ea_lease_payment_amount", "ea_lease_term", "ea_lease_principal_balance",
    "ea_lease_financed_amount", "ea_lease_rate_factor", "ea_lease_interest_rate",
    "ea_lease_schedule",
}
PROTECTED |= {f"ea_fleet_{k}" for k in (
    "machine_count", "meter_count", "monthly_volume", "volume_basis", "volume_period",
    "color_pct", "lifetime_pages", "contract_count", "lease_count", "open_calls",
    "next_expiry", "monthly_spend", "summary_updated")}

TECHS = ["R. Alvarez", "M. Okafor", "J. Lindqvist", "D. Pham", "S. Whitfield"]
DEPTS = ["Administration", "Finance", "Operations", "Clinical", "Legal", "Facilities"]
TERMS = ["Net 30", "Net 15", "Net 45", "Due on receipt"]


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
            txt = e.read()[:500].decode("utf-8", "replace")
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


def writable_props(obj: str) -> list[dict]:
    """ea_* properties this token may actually set."""
    r = call("GET", f"/crm/v3/properties/{urllib.parse.quote(obj)}")
    out = []
    for p in r.get("results", []):
        n = p["name"]
        if not n.startswith("ea_") or n in PROTECTED:
            continue
        mm = p.get("modificationMetadata") or {}
        # A calculated or read-only property 400s the whole batch, not just the row.
        if p.get("calculated") or mm.get("readOnlyValue"):
            continue
        out.append(p)
    return out


def page(obj: str, props: list[str]):
    after = None
    chunks = [props[i:i + 90] for i in range(0, len(props), 90)] or [[]]
    # HubSpot caps the property list per request, so read in slices and merge.
    merged: dict[str, dict] = {}
    for sl in chunks:
        after = None
        while True:
            q = {"limit": 100}
            if sl:
                q["properties"] = ",".join(sl)
            if after:
                q["after"] = after
            r = call("GET", f"/crm/v3/objects/{urllib.parse.quote(obj)}?"
                            + urllib.parse.urlencode(q))
            if "__error" in r:
                print(f"  ! read {obj}: {r['__error']} {r.get('__body','')[:160]}",
                      file=sys.stderr)
                break
            for rec in r.get("results", []):
                tgt = merged.setdefault(rec["id"], {"id": rec["id"], "properties": {}})
                tgt["properties"].update(rec.get("properties") or {})
            after = (r.get("paging") or {}).get("next", {}).get("after")
            if not after:
                break
    return list(merged.values())


def value_for(p: dict, rec: dict, label: str, seed: int):
    """A plausible value for this field, from its name and type."""
    n, typ = p["name"], p.get("type")
    field = p.get("fieldType")
    base = n[3:] if n.startswith("ea_") else n           # strip ea_
    props = rec.get("properties") or {}

    if typ == "enumeration":
        opts = [o["value"] for o in (p.get("options") or []) if o.get("value") not in (None, "")]
        if not opts:
            return None
        if field == "booleancheckbox" or set(opts) <= {"true", "false"}:
            return "true" if seed % 3 else "false"
        return opts[seed % len(opts)]

    if typ == "bool":
        return "true" if seed % 3 else "false"

    if typ in ("date", "datetime"):
        # Spread across a plausible window, deterministic per record and field.
        offset = -900 + (seed % 1400)
        if any(k in base for k in ("exp", "end", "due", "next", "renew")):
            offset = 30 + (seed % 900)
        return (TODAY + dt.timedelta(days=offset)).isoformat()

    if typ == "number":
        if "count" in base or "qty" in base or "quantity" in base:
            return str(1 + seed % 12)
        if "digit" in base:
            return "7"
        if "percent" in base or base.endswith("_pct"):
            return str(round(5 + (seed % 60), 1))
        if any(k in base for k in ("rate", "amount", "price", "cost", "balance", "total")):
            return f"{round(40 + (seed % 4000) + (seed % 97) / 100, 2)}"
        if "meter" in base or "copies" in base or "volume" in base or "page" in base:
            return str(1000 * (1 + seed % 60))
        if "id" in base:
            return str(1000 + seed % 9000)
        return str(1 + seed % 500)

    # ── strings, by what the name says it is ────────────────────────────────
    city = props.get("ea_city") or props.get("city") or "Columbus"
    state = props.get("ea_state") or props.get("state") or "OH"

    if base in ("city", "address_city"):
        return city
    if base in ("state", "address_state"):
        return state
    if base in ("zip", "address_zip", "postal_code"):
        return f"4{3000 + seed % 6000}"
    if base in ("country", "address_country"):
        return "United States"
    if "address" in base or "street" in base:
        return f"{100 + seed % 8800} {['Riverside','Kenwood','Halstead','Beaumont','Ashland'][seed % 5]} {['Ave','St','Blvd','Way'][seed % 4]}"
    if "email" in base:
        return f"{['a.reyes','k.donnelly','p.mbeki','l.zhang','t.okonkwo'][seed % 5]}@example.com"
    if "phone" in base or "fax" in base:
        return f"(614) {200 + seed % 700}-{1000 + seed % 8999}"
    if "technician" in base or "tech" in base:
        return TECHS[seed % len(TECHS)]
    if any(k in base for k in ("caller", "contact", "decision_maker", "attn", "rep", "name")):
        return ["A. Reyes", "K. Donnelly", "P. Mbeki", "L. Zhang", "T. Okonkwo"][seed % 5]
    if "term" in base:
        return TERMS[seed % len(TERMS)]
    if "department" in base or "dept" in base:
        return DEPTS[seed % len(DEPTS)]
    if "po_number" in base or base == "po":
        return f"PO-{40000 + seed % 9000}"
    if "status" in base:
        return ["Open", "Closed", "Pending", "Scheduled"][seed % 4]
    if "description" in base or "note" in base or "comment" in base:
        return f"{label} record populated for demonstration."
    if "location" in base:
        return f"{DEPTS[seed % len(DEPTS)]}, {['1st','2nd','3rd','Ground'][seed % 4]} floor"
    if "code" in base or base.endswith("_type") or "class" in base:
        return ["STD", "PRM", "SVC", "MFP"][seed % 4]
    if "model" in base:
        return ["MFP-C450", "MFP-B550", "PRT-M611", "MFP-C7081"][seed % 4]
    if "make" in base or "manufacturer" in base or "mfg" in base:
        return ["Canon", "Ricoh", "Konica Minolta", "Sharp", "Kyocera"][seed % 5]
    if "number" in base or base.endswith("_no"):
        return f"{base.upper().replace('_','-')}-{1000 + seed % 9000}"
    # Last resort: readable and obviously demo, never "x".
    return f"Demo {base.replace('_', ' ')}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    grand = 0
    for obj, key, label in OBJECTS:
        props = writable_props(obj)
        if not props:
            print(f"{label}: no writable ea_ properties", file=sys.stderr)
            continue
        names = [p["name"] for p in props] + [key]
        recs = [r for r in page(obj, names)
                if str((r["properties"] or {}).get(key) or "").startswith(PREFIX)]
        if not recs:
            print(f"{label}: no DEMO- records", file=sys.stderr)
            continue

        by_name = {p["name"]: p for p in props}
        updates, filled_fields = [], set()
        for rec in recs:
            cur = rec["properties"] or {}
            seed = sum(ord(ch) for ch in str(cur.get(key) or rec["id"]))
            patch = {}
            for i, name in enumerate(by_name):
                v = cur.get(name)
                if v not in (None, ""):
                    continue                       # never overwrite
                nv = value_for(by_name[name], rec, label, seed + i * 17)
                if nv is not None:
                    patch[name] = nv
                    filled_fields.add(name)
            if patch:
                updates.append({"id": rec["id"], "properties": patch})

        print(f"{label:14} {len(recs):4} records · {len(props):3} writable ea_ fields · "
              f"{len(updates):4} records to fill · {len(filled_fields):3} distinct fields",
              file=sys.stderr)

        if not args.apply or not updates:
            continue

        done = 0
        for i in range(0, len(updates), 100):
            chunk = updates[i:i + 100]
            r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/batch/update",
                     {"inputs": chunk})
            if "__error" in r:
                print(f"  ! {label} batch {i//100}: {r['__error']} "
                      f"{r.get('__body','')[:260]}", file=sys.stderr)
                # One bad property fails the whole batch, so retry per record to isolate
                # the damage rather than lose 100 good writes to one field.
                for one in chunk:
                    rr = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/batch/update",
                              {"inputs": [one]})
                    if "__error" not in rr:
                        done += len(rr.get("results", []))
                continue
            done += len(r.get("results", []))
        grand += done
        print(f"  {label}: {done}/{len(updates)} records filled", file=sys.stderr)

    print(f"\n{grand} records updated in total", file=sys.stderr)


if __name__ == "__main__":
    main()
