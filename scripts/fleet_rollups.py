#!/usr/bin/env python3
"""Roll the fleet up onto the Company record so a rep gets the account at a glance.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/fleet_rollups.py --plan
    python scripts/fleet_rollups.py --apply

WHY PROPERTIES AND NOT A TABLE. HubSpot's native association tables on a record can
only show STORED properties of the associated records. They cannot sum, average, count
or date-difference. So "12 machines, 501k pages a month, next contract expires in
March" is not expressible as an association table at any amount of configuration --
it has to be computed and written somewhere. Written here onto the Company, it shows
up as an ordinary property card with no app, no deploy and no CLI.

THE VOLUME NUMBER IS THE DANGEROUS ONE, AND IT DOES NOT COME FROM METERS.

Measured against this sandbox: EVERY volume field on ModelMeters is 0 -- 84 meters
across 120 machines, via the dedicated /api/MeterReadings/EquipmentMetersByEqNo route,
not the list route. avgMonthlyVolume3/6/12Mo, avgMonthlyVolumeInstall,
mfgSuggestedMonthlyVolume and targetMonthlyVolume are all zero. So a meter rollup here
produces 0, and 0 in a field called "monthly volume" is a number a rep will quote
against.

The volume that exists lives on /api/PrintReleaf/customers/{customerId}, which reports
pages actually produced inside a requested window -- Bank of America 2,932,596 lifetime,
ABC Company 82,501 in 2005-06. That route is the source of truth for volume, and it is
NOT the one a field-name-matching mapper would have picked.

The window matters and cannot be assumed. The route echoes back whatever range you ask
for and totals within it, so asking for a trailing twelve months in a sandbox whose
data stops in 2006 returns nothing -- which looks exactly like a customer that does not
print. This script therefore FINDS each customer's active period (decade, then year)
rather than trusting a fixed window, writes the monthly rate from the most recent active
year, and records that period next to the number.

Meters remain the fallback, because a production portal WILL have the rolling averages
that this sandbox lacks. Where they are used, note that e-automate's "Total Count" meter
is the SUM of the others (verified on EQ100248: B/W 10,000 + Color 5,000 = Total 15,000),
so a Total-type meter supersedes the component meters instead of adding to them.

A figure whose provenance is not visible next to it is worse than a blank, because a
blank prompts a question and a wrong number does not.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
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
METER = "2-66645402"
SERVICE_CALL = "2-66645395"

GROUP = "e_automate_fleet"

# Meter type codes that already represent the machine total. Anything else is a
# component meter and may be summed.
TOTAL_CODES = {"total", "totalcount", "total count", "t", "tc"}

PROPS = [
    ("ea_fleet_machine_count", "e-auto Fleet: Machines", "number", "number",
     "Associated Equipment records carrying an e-automate equipment number."),
    ("ea_fleet_meter_count", "e-auto Fleet: Meters", "number", "number",
     "Associated Meter records. Higher than the machine count because most devices "
     "carry several meters."),
    ("ea_fleet_monthly_volume", "e-auto Fleet: Monthly Volume", "number", "number",
     "Estimated pages per month across the fleet. Read the basis property next to "
     "this before quoting it."),
    ("ea_fleet_volume_basis", "e-auto Fleet: Volume Basis", "enumeration", "select",
     "Where the volume figure came from. 'Manufacturer rated' is a duty cycle, not a "
     "measurement of this customer's printing."),
    ("ea_fleet_volume_period", "e-auto Fleet: Volume Period", "string", "text",
     "The window the volume figure was measured over. A monthly rate derived from an "
     "old period is a historical rate, not a current one."),
    ("ea_fleet_color_pct", "e-auto Fleet: Colour Share %", "number", "number",
     "Colour pages as a percentage of total. The single most useful number for "
     "deciding whether a colour device is justified."),
    ("ea_fleet_lifetime_pages", "e-auto Fleet: Lifetime Pages", "number", "number",
     "All pages PrintReleaf has ever recorded for this customer."),
    ("ea_fleet_contract_count", "e-auto Fleet: Contracts", "number", "number", None),
    ("ea_fleet_lease_count", "e-auto Fleet: Leases", "number", "number", None),
    ("ea_fleet_open_calls", "e-auto Fleet: Open Service Calls", "number", "number", None),
    ("ea_fleet_next_expiry", "e-auto Fleet: Next Contract Expiry", "date", "date",
     "Earliest expiry across the customer's contracts -- the date the renewal "
     "conversation is driven by."),
    ("ea_fleet_monthly_spend", "e-auto Fleet: Monthly Spend", "number", "number",
     "Contract base rates plus lease payments per month. Excludes overage, which is "
     "not exposed as a rate on any route."),
    ("ea_fleet_summary_updated", "e-auto Fleet: Summary Calculated", "date", "date",
     "When these rollups were last computed. They are a snapshot, not live."),
]

VOLUME_BASIS = [
    ("printreleaf_current", "PrintReleaf - trailing 12 months"),
    ("printreleaf_historic", "PrintReleaf - most recent active year"),
    ("actual_12mo", "Meters - 12-month actual"),
    ("actual_shorter", "Meters - 3 or 6-month actual"),
    ("since_install", "Meters - average since install"),
    ("mfg_rated", "Manufacturer rated (a duty cycle, not a measurement)"),
    ("target", "Target volume"),
    ("unknown", "Unknown - no reading history"),
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
        r = call("GET", f"/crm/v3/objects/{urllib.parse.quote(obj)}?"
                        + urllib.parse.urlencode(q))
        if "__error" in r:
            sys.exit(f"read {obj}: {r['__error']} {r.get('__body','')}")
        yield from r.get("results", [])
        after = (r.get("paging") or {}).get("next", {}).get("after")
        if not after:
            return


def ensure_group() -> None:
    r = call("POST", f"/crm/v3/properties/{COMPANY}/groups",
             {"name": GROUP, "label": "e-Automate Fleet Summary", "displayOrder": -1})
    if "__error" in r and r["__error"] != 409:
        print(f"  group: {r['__error']} {r.get('__body','')[:160]}", file=sys.stderr)
    else:
        print(f"  group {GROUP}: {'exists' if r.get('__error') == 409 else 'created'}",
              file=sys.stderr)


def ensure_props(apply: bool) -> None:
    have = {p["name"] for p in call("GET", f"/crm/v3/properties/{COMPANY}")
            .get("results", [])}
    for name, label, typ, field, desc in PROPS:
        if name in have:
            print(f"  {name}: exists", file=sys.stderr)
            continue
        if not apply:
            print(f"  {name}: WOULD CREATE ({typ})", file=sys.stderr)
            continue
        body = {"name": name, "label": label, "type": typ, "fieldType": field,
                "groupName": GROUP}
        if desc:
            body["description"] = desc
        if typ == "enumeration":
            body["options"] = [{"label": lb, "value": v, "displayOrder": i}
                              for i, (v, lb) in enumerate(VOLUME_BASIS)]
        r = call("POST", f"/crm/v3/properties/{COMPANY}", body)
        if "__error" in r and r["__error"] != 409:
            print(f"  {name}: FAILED {r['__error']} {r.get('__body','')[:200]}",
                  file=sys.stderr)
        else:
            print(f"  {name}: created", file=sys.stderr)


def assoc(frm: str, to: str, ids: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in range(0, len(ids), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/read",
                 {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        for res in (r.get("results") or []):
            out[res["from"]["id"]] = [str(t["toObjectId"]) for t in res.get("to", [])]
    return out


def num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def machine_volume(meters: list[dict]) -> tuple[float, str]:
    """One machine's monthly volume, and the basis it came from.

    Total-type meters supersede component meters rather than adding to them, because
    e-automate's Total Count IS the sum of the others."""
    totals = [m for m in meters
              if str((m.get("properties") or {}).get("ea_meter_type_code") or "")
              .strip().lower() in TOTAL_CODES]
    use = totals or meters

    for prop, basis in (("ea_avg_monthly_volume12_mo", "actual_12mo"),
                        ("ea_avg_monthly_volume6_mo", "actual_shorter"),
                        ("ea_avg_monthly_volume3_mo", "actual_shorter"),
                        ("ea_avg_monthly_volume_install", "since_install"),
                        ("ea_mfg_suggested_monthly_volume", "mfg_rated"),
                        ("ea_target_monthly_volume", "target")):
        vals = [num((m.get("properties") or {}).get(prop)) for m in use]
        vals = [v for v in vals if v and v > 0]      # 0 is unknown, never a reading
        if vals:
            return (sum(vals), basis)
    return (0.0, "unknown")


BASIS_RANK = {"unknown": 0, "target": 1, "mfg_rated": 2, "since_install": 3,
              "actual_shorter": 4, "actual_12mo": 5,
              "printreleaf_historic": 6, "printreleaf_current": 7}


def pr_total(cj, customer_id: int, y0: int, y1: int) -> tuple[float, float, float]:
    """(total, bw, colour) pages produced between 1 Jan y0 and 31 Dec y1."""
    try:
        rows = cj.page_volumes(customer_id, dt.datetime(y0, 1, 1),
                               dt.datetime(y1, 12, 31)) or []
    except Exception:  # noqa: BLE001 - one customer must not kill the run
        return (0.0, 0.0, 0.0)
    t = sum(float(r.get("totalPages") or 0) for r in rows)
    b = sum(float(r.get("blackAndWhitePages") or 0) for r in rows)
    c = sum(float(r.get("colorPages") or 0) for r in rows)
    return (t, b, c)


def printreleaf_volume(cj, customer_id: int, this_year: int):
    """Monthly page rate for a customer, plus how it was arrived at.

    Returns (monthly, basis, period_label, colour_pct, lifetime) or None.

    The search is deliberate rather than a fixed window: the route totals whatever range
    it is given, so a trailing-12-month query against a dataset that ends in 2006 returns
    zero and is indistinguishable from a customer who does not print. Cost is ~3 calls
    for the decade sweep plus up to 10 to find the year -- paid once per customer.
    """
    lifetime, lb, lc = pr_total(cj, customer_id, 2000, this_year + 1)
    if lifetime <= 0:
        return None
    colour_pct = round(100.0 * lc / lifetime, 1) if lifetime else 0.0

    # Production-correct answer first: a real trailing twelve months.
    cur, cb, cc = pr_total(cj, customer_id, this_year - 1, this_year)
    if cur > 0:
        pct = round(100.0 * cc / cur, 1) if cur else colour_pct
        return (cur / 24.0, "printreleaf_current",
                f"{this_year - 1}-{this_year} trailing", pct, lifetime)

    # Otherwise locate the active period: decade, then year inside it.
    decades = [(2020, this_year + 1), (2010, 2019), (2000, 2009)]
    for y0, y1 in decades:
        t, _, _ = pr_total(cj, customer_id, y0, y1)
        if t <= 0:
            continue
        for y in range(min(y1, this_year + 1), y0 - 1, -1):
            ty, byw, cy = pr_total(cj, customer_id, y, y)
            if ty > 0:
                pct = round(100.0 * cy / ty, 1) if ty else colour_pct
                return (ty / 12.0, "printreleaf_historic", str(y), pct, lifetime)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("properties:", file=sys.stderr)
    if args.apply:
        ensure_group()
    ensure_props(args.apply)

    print("\nreading portal ...", file=sys.stderr)
    companies = [c for c in page(COMPANY, ["name", "ea_customer_number"])
                 if (c.get("properties") or {}).get("ea_customer_number")]
    equipment = {r["id"]: r for r in page(EQUIPMENT, ["ea_equipment_number"])}
    contracts = {r["id"]: r for r in page(CONTRACT,
                                          ["ea_contract_number", "ea_exp_date",
                                           "base_rate", "ea_base_rate_period"])}
    leases = {r["id"]: r for r in page(LEASE, ["ea_contract_detail_id",
                                               "ea_lease_payment_amount"])}
    meters = {r["id"]: r for r in page(METER,
                                       ["ea_equipment_number", "ea_meter_type_code",
                                        "ea_avg_monthly_volume12_mo",
                                        "ea_avg_monthly_volume6_mo",
                                        "ea_avg_monthly_volume3_mo",
                                        "ea_avg_monthly_volume_install",
                                        "ea_mfg_suggested_monthly_volume",
                                        "ea_target_monthly_volume"])}
    calls = {r["id"]: r for r in page(SERVICE_CALL, ["ea_call_number", "ea_status"])}
    print(f"  {len(companies)} e-automate companies, {len(equipment)} machines, "
          f"{len(contracts)} contracts, {len(leases)} leases, {len(meters)} meters, "
          f"{len(calls)} calls", file=sys.stderr)

    cids = [c["id"] for c in companies]
    a_eq = assoc(COMPANY, EQUIPMENT, cids)
    a_cn = assoc(COMPANY, CONTRACT, cids)
    a_ls = assoc(COMPANY, LEASE, cids)
    a_me = assoc(COMPANY, METER, cids)
    a_sc = assoc(COMPANY, SERVICE_CALL, cids)

    # Meters grouped per machine, so Total-vs-component can be judged per device
    # rather than across the whole fleet.
    eq_meters = assoc(EQUIPMENT, METER, list(equipment))

    # PrintReleaf is keyed on customerId, the portal on customerNumber.
    cj = CeoJuiceClient()
    pr_id = {str(r.get("customerNumber")): r.get("customerId")
             for r in cj.printreleaf_customers()}
    print(f"  {len(pr_id)} PrintReleaf customers", file=sys.stderr)

    today = dt.date.today().isoformat()
    this_year = dt.date.today().year
    updates, preview = [], []
    for c in companies:
        cid = c["id"]
        eq_ids = [e for e in a_eq.get(cid, []) if e in equipment]
        cn_ids = [x for x in a_cn.get(cid, []) if x in contracts]
        ls_ids = [x for x in a_ls.get(cid, []) if x in leases]
        sc_ids = [x for x in a_sc.get(cid, []) if x in calls]

        # Volume per machine via the machine's own meters; fall back to the
        # company-linked meters for machines that carry no Equipment edge.
        vol, bases = 0.0, []
        seen: set[str] = set()
        for e in eq_ids:
            ms = [meters[m] for m in eq_meters.get(e, []) if m in meters]
            seen.update(eq_meters.get(e, []))
            if ms:
                v, b = machine_volume(ms)
                vol += v
                bases.append(b)
        loose = [meters[m] for m in a_me.get(cid, [])
                 if m in meters and m not in seen]
        by_machine = collections.defaultdict(list)
        for m in loose:
            by_machine[(m.get("properties") or {}).get("ea_equipment_number")].append(m)
        for ms in by_machine.values():
            v, b = machine_volume(ms)
            vol += v
            bases.append(b)

        meter_total = len({*a_me.get(cid, []), *(m for e in eq_ids
                                                 for m in eq_meters.get(e, []))})
        # Report the WEAKEST basis contributing, not the best: the number is only as
        # trustworthy as its softest component.
        basis = min(bases, key=lambda b: BASIS_RANK[b]) if bases else "unknown"
        period, colour_pct, lifetime = "", None, None

        # PrintReleaf beats any meter rollup where it has data, because it reports pages
        # actually produced rather than a rate e-automate failed to compute.
        cust_no = (c.get("properties") or {}).get("ea_customer_number")
        pv = printreleaf_volume(cj, pr_id[str(cust_no)], this_year) \
            if str(cust_no) in pr_id else None
        if pv:
            vol, basis, period, colour_pct, lifetime = pv

        expiries = sorted(x for x in
                          ((contracts[i].get("properties") or {}).get("ea_exp_date")
                           for i in cn_ids) if x)
        spend = 0.0
        for i in cn_ids:
            p = contracts[i].get("properties") or {}
            r = num(p.get("base_rate"))
            if r:
                per = str(p.get("ea_base_rate_period") or "").strip().lower()
                spend += r / 12 if per.startswith("y") else r
        for i in ls_ids:
            r = num((leases[i].get("properties") or {}).get("ea_lease_payment_amount"))
            if r:
                spend += r
        open_calls = sum(1 for i in sc_ids
                         if not str((calls[i].get("properties") or {})
                                    .get("ea_status") or "").strip().upper()
                         .startswith("C"))

        props = {
            "ea_fleet_machine_count": len(eq_ids),
            "ea_fleet_meter_count": meter_total,
            "ea_fleet_monthly_volume": int(round(vol)),
            "ea_fleet_volume_basis": basis,
            "ea_fleet_contract_count": len(cn_ids),
            "ea_fleet_lease_count": len(ls_ids),
            "ea_fleet_open_calls": open_calls,
            "ea_fleet_monthly_spend": round(spend, 2),
            "ea_fleet_summary_updated": today,
        }
        if expiries:
            props["ea_fleet_next_expiry"] = expiries[0][:10]
        if period:
            props["ea_fleet_volume_period"] = period
        if colour_pct is not None:
            props["ea_fleet_color_pct"] = colour_pct
        if lifetime is not None:
            props["ea_fleet_lifetime_pages"] = int(round(lifetime))
        updates.append((cid, {k: str(v) for k, v in props.items()}))
        preview.append((c["properties"].get("name"), len(eq_ids), meter_total,
                        int(round(vol)), basis, period, colour_pct,
                        len(cn_ids), len(ls_ids),
                        open_calls, round(spend, 2),
                        expiries[0][:10] if expiries else "-"))

    preview.sort(key=lambda r: -r[3])
    print(f"\n{'company':30} {'mach':>4} {'mtr':>4} {'vol/mo':>9} {'basis':<21}"
          f" {'period':<9} {'col%':>5} {'cn':>3} {'ls':>3} {'call':>4} {'spend/mo':>9}",
          file=sys.stderr)
    for r in preview[:16]:
        print(f"{str(r[0])[:30]:30} {r[1]:4} {r[2]:4} {r[3]:9,} {r[4]:<21}"
              f" {str(r[5] or '-'):<9} {(str(r[6]) if r[6] is not None else '-'):>5}"
              f" {r[7]:3} {r[8]:3} {r[9]:4} {r[10]:9,.0f}", file=sys.stderr)

    if not args.apply:
        print(f"\n--plan only. {len(updates)} companies would be updated.", file=sys.stderr)
        return

    done = 0
    for i in range(0, len(updates), 100):
        chunk = updates[i:i + 100]
        r = call("POST", f"/crm/v3/objects/{COMPANY}/batch/update",
                 {"inputs": [{"id": cid, "properties": p} for cid, p in chunk]})
        if "__error" in r:
            print(f"  ! batch {i//100}: {r['__error']} {r.get('__body','')[:300]}",
                  file=sys.stderr)
            continue
        done += len(r.get("results", []))
        for e in (r.get("errors") or []):
            print(f"  ! {str(e)[:200]}", file=sys.stderr)
    print(f"\n{done}/{len(updates)} companies updated", file=sys.stderr)

    # Read it back: a 207 is a success status that hides per-row failures.
    v = call("POST", f"/crm/v3/objects/{COMPANY}/search",
             {"limit": 1, "properties": ["hs_object_id"],
              "filterGroups": [{"filters": [{"propertyName": "ea_fleet_machine_count",
                                             "operator": "HAS_PROPERTY"}]}]})
    print(f"VERIFY ea_fleet_machine_count filled on {v.get('total')} companies",
          file=sys.stderr)


if __name__ == "__main__":
    main()
