#!/usr/bin/env python3
"""Add the two things the account review could not answer: service cost and cost per page.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/seed_demo_costs.py --apply

WHAT WAS MISSING AND WHY IT MATTERED.

Cost per page was the biggest hole in the review. Spend could only ever be contract base
rate plus lease payment, which EXCLUDES overage -- and overage is usually most of the bill.
"You are paying 2.1 cents and I will do 1.4" is the entire pitch of a fleet review, and it
needs invoiced revenue, which nothing synced: the Invoice object carried one property
(ea_invoice_number) and zero records.

Service COUNT was in the review; service COST was not. "17 calls" is suggestive. "$4,200 of
labour and parts on a machine worth $1,800" closes, and it is the difference between a
reviewer nodding and a reviewer signing.

Both are seeded for the DEMO- accounts only, from the fixture's own volumes, so the numbers
are internally consistent: invoiced revenue is derived from each device's real metered
volume at a plausible contracted rate plus overage, rather than picked. That means the cost
per page the screen computes is arithmetically true about this dataset rather than a
constant typed into a field.

Real accounts are untouched. They will show cost per page as soon as invoices sync, and
show it as absent until then -- which is the correct behaviour and the reason the figure is
computed rather than stored.
"""

from __future__ import annotations

import argparse
import datetime as dt
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
INVOICE = "2-66645175"
SERVICE_CALL = "2-66645395"
GROUP = "e_automate"
PREFIX = "DEMO-"
TODAY = dt.date(2026, 7, 30)

INVOICE_PROPS = [
    ("ea_invoice_amount", "e-auto Invoice Amount", "number", "number",
     "Total invoiced. The only route to a true cost per page, because it includes the "
     "overage that a contract base rate leaves out."),
    ("ea_invoice_date", "e-auto Invoice Date", "date", "date", None),
    ("ea_customer_number", "e-auto Customer Number", "string", "text", None),
    ("ea_invoice_base_amount", "e-auto Invoice Base Amount", "number", "number",
     "The contracted portion, before overage."),
    ("ea_invoice_overage_amount", "e-auto Invoice Overage Amount", "number", "number",
     "Billed above the contract allowance. Usually where the margin is, and invisible "
     "in a base-rate-only view of spend."),
]

CALL_PROPS = [
    ("ea_call_labor_cost", "e-auto Call Labour Cost", "number", "number",
     "Labour billed or absorbed on this call."),
    ("ea_call_parts_cost", "e-auto Call Parts Cost", "number", "number", None),
    ("ea_call_total_cost", "e-auto Call Total Cost", "number", "number",
     "Labour plus parts. Rolled up per device so a service history can be argued in "
     "money rather than in call count."),
]

# Contracted rate per page, and the overage rate above allowance. Mono and colour are
# priced very differently, which is why a fleet's colour share drives its bill.
RATE_BW, RATE_CLR = 0.0089, 0.0641
OVER_BW, OVER_CLR = 0.0121, 0.0795


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


def ensure(obj: str, props, label: str) -> None:
    have = {p["name"] for p in call("GET", f"/crm/v3/properties/{obj}").get("results", [])}
    for name, lbl, typ, field, desc in props:
        if name in have:
            continue
        body = {"name": name, "label": lbl, "type": typ, "fieldType": field,
                "groupName": GROUP}
        if desc:
            body["description"] = desc
        r = call("POST", f"/crm/v3/properties/{obj}", body)
        ok = "created" if "__error" not in r or r.get("__error") == 409 else \
            f"FAILED {r['__error']} {r.get('__body','')[:120]}"
        print(f"  {label}.{name}: {ok}", file=sys.stderr)


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


def assoc_type(frm: str, to: str):
    r = call("GET", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                    f"{urllib.parse.quote(to)}/labels")
    if "__error" in r:
        return None
    for t in r.get("results", []):
        if t.get("label") is None:
            return t["typeId"]
    res = r.get("results", [])
    return res[0]["typeId"] if res else None


def link(frm: str, to: str, pairs, label: str) -> None:
    if not pairs:
        return
    tid = assoc_type(frm, to)
    if tid is None:
        print(f"  {label}: no definition, skipped", file=sys.stderr)
        return
    made = 0
    for i in range(0, len(pairs), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/create",
                 {"inputs": [{"from": {"id": a}, "to": {"id": b},
                              "types": [{"associationCategory": "USER_DEFINED",
                                         "associationTypeId": tid}]}
                             for a, b in pairs[i:i + 100]]})
        if "__error" in r:
            print(f"  ! {label}: {r['__error']} {r.get('__body','')[:200]}", file=sys.stderr)
            continue
        made += len(r.get("results", []))
    print(f"  {label}: {made}/{len(pairs)} edges", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("properties ...", file=sys.stderr)
    if args.apply:
        ensure(INVOICE, INVOICE_PROPS, "Invoice")
        ensure(SERVICE_CALL, CALL_PROPS, "ServiceCall")

    # Demo companies and their devices' metered volume, so invoiced revenue is derived
    # from the same numbers the review displays.
    companies = {}
    for c in page(COMPANY, ["name", "ea_customer_number", "ea_fleet_monthly_volume",
                            "ea_fleet_color_pct"]):
        n = (c.get("properties") or {}).get("ea_customer_number") or ""
        if str(n).startswith(PREFIX):
            companies[str(n)] = c
    print(f"\n{len(companies)} demo companies", file=sys.stderr)

    calls = [c for c in page(SERVICE_CALL, ["ea_call_number", "ea_status", "ea_date"])
             if str((c.get("properties") or {}).get("ea_call_number") or "").startswith(PREFIX)]
    print(f"{len(calls)} demo service calls", file=sys.stderr)

    if not args.apply:
        print("\n--plan only.", file=sys.stderr)
        return

    # ── service cost ────────────────────────────────────────────────────────
    # Varied but deterministic: the same call always gets the same figure, so a demo is
    # stable across reruns and nobody chases a number that moved on its own.
    updates = []
    for c in calls:
        no = str(c["properties"]["ea_call_number"])
        seed = sum(ord(ch) for ch in no)
        labour = 85.0 + (seed % 7) * 47.5
        parts = float((seed % 13) * 63)
        updates.append({"id": c["id"], "properties": {
            "ea_call_labor_cost": f"{labour:.2f}",
            "ea_call_parts_cost": f"{parts:.2f}",
            "ea_call_total_cost": f"{labour + parts:.2f}",
        }})
    done = 0
    for i in range(0, len(updates), 100):
        r = call("POST", f"/crm/v3/objects/{SERVICE_CALL}/batch/update",
                 {"inputs": updates[i:i + 100]})
        if "__error" in r:
            print(f"  ! calls: {r['__error']} {r.get('__body','')[:200]}", file=sys.stderr)
            continue
        done += len(r.get("results", []))
    print(f"\nservice cost written to {done}/{len(updates)} calls", file=sys.stderr)

    # ── invoices: 12 monthly bills per demo company ─────────────────────────
    # Base plus overage, derived from the company's own metered volume. Overage appears
    # in the months a fleet ran hot, which is what makes the annual figure exceed 12x the
    # base rate -- the exact effect a base-rate-only view of spend hides.
    inv_rows, inv_owner = [], []
    for num, c in companies.items():
        p = c["properties"]
        vol = float(p.get("ea_fleet_monthly_volume") or 0)
        clr_pct = float(p.get("ea_fleet_color_pct") or 0) / 100.0
        clr = vol * clr_pct
        bw = vol - clr
        for m in range(12):
            when = TODAY - dt.timedelta(days=30 * m + 5)
            # Seasonal swing, deterministic per company and month.
            swing = 1.0 + (((sum(ord(x) for x in num) + m * 7) % 9) - 4) / 40.0
            mb, mc = bw * swing, clr * swing
            base = mb * RATE_BW + mc * RATE_CLR
            over = 0.0
            if swing > 1.03:                     # ran above allowance that month
                over = (mb * 0.11 * OVER_BW) + (mc * 0.11 * OVER_CLR)
            no = f"{PREFIX}INV-{num.replace(PREFIX,'')}-{when.strftime('%Y%m')}"
            inv_rows.append({"properties": {
                "ea_invoice_number": no,
                "ea_invoice_date": when.isoformat(),
                "ea_invoice_amount": f"{base + over:.2f}",
                "ea_invoice_base_amount": f"{base:.2f}",
                "ea_invoice_overage_amount": f"{over:.2f}",
                "ea_customer_number": num,
            }})
            inv_owner.append((no, num))

    inv_ids: dict[str, str] = {}
    for i in range(0, len(inv_rows), 100):
        chunk = inv_rows[i:i + 100]
        r = call("POST", f"/crm/v3/objects/{INVOICE}/batch/upsert",
                 {"inputs": [{"idProperty": "ea_invoice_number",
                              "id": x["properties"]["ea_invoice_number"],
                              "properties": x["properties"]} for x in chunk]})
        if "__error" in r:
            print(f"  ! invoices: {r['__error']} {r.get('__body','')[:300]}", file=sys.stderr)
            continue
        for res in r.get("results", []):
            k = (res.get("properties") or {}).get("ea_invoice_number")
            if k:
                inv_ids[str(k)] = str(res["id"])
    print(f"invoices upserted: {len(inv_ids)}/{len(inv_rows)}", file=sys.stderr)

    link(COMPANY, INVOICE,
         [(companies[num]["id"], inv_ids[no]) for no, num in inv_owner if no in inv_ids],
         "Company -> Invoice")

    # Read it back per company rather than trusting the batch statuses.
    print("\nVERIFY", file=sys.stderr)
    for num, c in companies.items():
        r = call("GET", f"/crm/v4/objects/companies/{c['id']}/associations/"
                        f"{urllib.parse.quote(INVOICE)}?limit=100")
        ids = [str(x["toObjectId"]) for x in r.get("results", [])]
        tot = 0.0
        if ids:
            b = call("POST", f"/crm/v3/objects/{INVOICE}/batch/read",
                     {"properties": ["ea_invoice_amount"],
                      "inputs": [{"id": x} for x in ids]})
            tot = sum(float((x["properties"] or {}).get("ea_invoice_amount") or 0)
                      for x in b.get("results", []))
        vol = float(c["properties"].get("ea_fleet_monthly_volume") or 0)
        cpp = (tot / (vol * 12)) if vol else 0
        print(f"  {str(c['properties'].get('name'))[:26]:26} {len(ids):3} invoices  "
              f"${tot:10,.0f}/yr   implied CPP {cpp*100:.3f}c", file=sys.stderr)


if __name__ == "__main__":
    main()
