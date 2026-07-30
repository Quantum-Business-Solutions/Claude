#!/usr/bin/env python3
"""Seed three fully-populated demo accounts so the account review can be seen working.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/seed_demo_accounts.py --plan
    python scripts/seed_demo_accounts.py --apply
    python scripts/seed_demo_accounts.py --delete     # remove every DEMO- record

WHY THIS EXISTS. The e-automate sandbox cannot show what this screen does. Measured: 0 of
120 meters carry a non-zero volume on any field, 1 of 45 leases carries any terms, the
newest contract expiry in the data is 2017, and no invoice exists at all. So a real review
-- volumes per device, months remaining on a lease, a contract expiring next quarter --
cannot be demonstrated from it however well the code works.

THIS DATA IS SYNTHETIC AND IS MARKED SO IT CANNOT BE MISTAKEN OTHERWISE.
  - Every record's key is prefixed DEMO- (DEMO-CUST-01, DEMO-EQ-0101, DEMO-C-0101 ...).
  - Company names are the standard fictional set (Northwind, Contoso, Fabrikam), which no
    dealer will confuse with a customer.
  - --delete removes exactly the DEMO- prefixed records and nothing else.
A demo fixture that looks like production data is a liability: somebody quotes from it, or
a later engineer treats it as evidence about the API. The prefix is the whole safeguard.

EACH ACCOUNT TELLS A DIFFERENT STORY, because a fleet review is a sales argument and the
screen should be exercised by the arguments it has to support:
  Northwind   the ordinary renewal -- healthy fleet, one contract expiring in 4 months.
  Contoso     the messy real one -- an EXPIRED contract, two devices on no contract at all
              (the whitespace), and two old machines over their duty cycle with heavy
              service history (the replacement case).
  Fabrikam    the downsize -- four devices massively over-specced for what they print.

REQUIRED PROPERTIES ARE SET EXPLICITLY. Creating into Contract without `contractnumber`
AND `contract_type` returns 400 for the whole batch -- this portal's Contract object
requires both, and a previous run of the real sync produced 1,220 identical failures
learning that. Meter requires ea_meter_key, Service Call requires ea_call_number.
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
CONTRACT = "2-36237359"
LEASE = "2-50535055"
METER = "2-66645402"
SERVICE_CALL = "2-66645395"

PREFIX = "DEMO-"
TODAY = dt.date(2026, 7, 30)


def d(days: int) -> str:
    return (TODAY + dt.timedelta(days=days)).isoformat()


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


# ─────────────────────────────────────────────────────────────────────────────
# The fixture. Volumes are what these machines actually run in the field: a
# production colour MFP at 30-45k/month, a mono workhorse at 12-25k, a desktop at
# 1-4k. Duty cycles are the manufacturers' published monthly maximums, which is what
# makes over-utilisation visible -- a device at 140% of rating is the single strongest
# replacement argument there is, and it needs both numbers to be sayable.
# ─────────────────────────────────────────────────────────────────────────────
ACCOUNTS = [
    {
        "num": "CUST-01", "name": "Northwind Traders", "city": "Columbus", "state": "OH",
        "domain": "northwindtraders.example",
        "story": "Ordinary renewal: healthy fleet, one contract expiring in four months.",
        "contracts": [
            {"id": "C-0101", "type": "Full Service", "start": -730, "exp": 123,
             "rate": 1480.0, "period": "1", "renewable": True, "copies": 240000,
             "unearned": 4920.0},
            {"id": "C-0102", "type": "Full Service", "start": -390, "exp": 640,
             "rate": 615.0, "period": "1", "renewable": True, "copies": 96000,
             "unearned": 8300.0},
        ],
        "devices": [
            {"id": "EQ-0101", "serial": "CN8842119", "make": "Canon", "model": "imageRUNNER ADVANCE DX C5860i",
             "loc": "2nd floor copy room", "install": -700, "warranty": 400,
             "bw": 18400, "clr": 9600, "duty": 40000, "contract": "C-0101",
             "lease": "L-0101", "calls": 2},
            {"id": "EQ-0102", "serial": "CN8842204", "make": "Canon", "model": "imageRUNNER ADVANCE DX C3835i",
             "loc": "Accounting", "install": -700, "warranty": 400,
             "bw": 11200, "clr": 4100, "duty": 25000, "contract": "C-0101",
             "lease": "L-0101", "calls": 1},
            {"id": "EQ-0103", "serial": "RX2210884", "make": "Ricoh", "model": "IM 430F",
             "loc": "Reception", "install": -640, "warranty": 460,
             "bw": 3100, "clr": 0, "duty": 8000, "contract": "C-0101",
             "lease": "L-0102", "calls": 0},
            {"id": "EQ-0104", "serial": "RX2210917", "make": "Ricoh", "model": "IM C300F",
             "loc": "Sales bullpen", "install": -640, "warranty": 460,
             "bw": 6400, "clr": 3900, "duty": 15000, "contract": "C-0101",
             "lease": "L-0102", "calls": 3},
            {"id": "EQ-0105", "serial": "KM4471203", "make": "Konica Minolta", "model": "bizhub C450i",
             "loc": "Warehouse office", "install": -380, "warranty": 720,
             "bw": 9700, "clr": 5200, "duty": 30000, "contract": "C-0102",
             "lease": "L-0103", "calls": 1},
            {"id": "EQ-0106", "serial": "KM4471288", "make": "Konica Minolta", "model": "bizhub 4750i",
             "loc": "Shipping desk", "install": -380, "warranty": 720,
             "bw": 14300, "clr": 0, "duty": 20000, "contract": "C-0102",
             "lease": "L-0103", "calls": 0},
            {"id": "EQ-0107", "serial": "HP9920551", "make": "HP", "model": "LaserJet Enterprise M611dn",
             "loc": "Executive suite", "install": -300, "warranty": 800,
             "bw": 2300, "clr": 0, "duty": 7500, "contract": "C-0102",
             "lease": None, "calls": 0},
            {"id": "EQ-0108", "serial": "HP9920604", "make": "HP", "model": "Color LaserJet Enterprise M555dn",
             "loc": "Marketing", "install": -300, "warranty": 800,
             "bw": 1900, "clr": 2600, "duty": 6000, "contract": "C-0102",
             "lease": None, "calls": 1},
        ],
        "leases": [
            {"id": "L-0101", "schedule": "NW-4471-A", "term": 60, "start": -700, "end": 1125,
             "payment": 742.18, "financed": 38400.0, "principal": 24180.55,
             "factor": 0.01933, "rate": 6.9},
            {"id": "L-0102", "schedule": "NW-4471-B", "term": 60, "start": -640, "end": 1185,
             "payment": 388.40, "financed": 20100.0, "principal": 13260.75,
             "factor": 0.01932, "rate": 6.9},
            {"id": "L-0103", "schedule": "NW-5502-A", "term": 48, "start": -380, "end": 1080,
             "payment": 611.05, "financed": 26800.0, "principal": 20940.10,
             "factor": 0.02280, "rate": 7.4},
        ],
    },
    {
        "num": "CUST-02", "name": "Contoso Health Systems", "city": "Rochester", "state": "MN",
        "domain": "contosohealth.example",
        "story": "The messy one: an expired contract, two devices on nothing, "
                 "two machines over duty cycle with heavy service history.",
        "contracts": [
            {"id": "C-0201", "type": "Full Service", "start": -1460, "exp": -121,
             "rate": 2980.0, "period": "1", "renewable": True, "copies": 720000,
             "unearned": 0.0},
            {"id": "C-0202", "type": "Full Service", "start": -580, "exp": 245,
             "rate": 1875.0, "period": "1", "renewable": True, "copies": 420000,
             "unearned": 15400.0},
            {"id": "C-0203", "type": "Parts & Labour", "start": -200, "exp": 895,
             "rate": 940.0, "period": "1", "renewable": False, "copies": 180000,
             "unearned": 22600.0},
        ],
        "devices": [
            {"id": "EQ-0201", "serial": "XR7730114", "make": "Xerox", "model": "AltaLink C8170",
             "loc": "Medical records", "install": -1430, "warranty": -330,
             "bw": 41200, "clr": 12800, "duty": 40000, "contract": "C-0201",
             "lease": "L-0201", "calls": 9},
            {"id": "EQ-0202", "serial": "XR7730188", "make": "Xerox", "model": "AltaLink B8145",
             "loc": "Billing", "install": -1430, "warranty": -330,
             "bw": 33600, "clr": 0, "duty": 25000, "contract": "C-0201",
             "lease": "L-0201", "calls": 7},
            {"id": "EQ-0203", "serial": "SH5541027", "make": "Sharp", "model": "MX-7081",
             "loc": "Central print", "install": -560, "warranty": 540,
             "bw": 52400, "clr": 21700, "duty": 100000, "contract": "C-0202",
             "lease": "L-0202", "calls": 3},
            {"id": "EQ-0204", "serial": "SH5541093", "make": "Sharp", "model": "MX-6071",
             "loc": "Radiology", "install": -560, "warranty": 540,
             "bw": 28900, "clr": 14200, "duty": 60000, "contract": "C-0202",
             "lease": "L-0202", "calls": 2},
            {"id": "EQ-0205", "serial": "SH5541140", "make": "Sharp", "model": "MX-3071",
             "loc": "Ward 4 nurses station", "install": -540, "warranty": 560,
             "bw": 8800, "clr": 3300, "duty": 20000, "contract": "C-0202",
             "lease": "L-0203", "calls": 1},
            {"id": "EQ-0206", "serial": "SH5541201", "make": "Sharp", "model": "MX-3071",
             "loc": "Ward 6 nurses station", "install": -540, "warranty": 560,
             "bw": 7900, "clr": 2800, "duty": 20000, "contract": "C-0202",
             "lease": "L-0203", "calls": 0},
            {"id": "EQ-0207", "serial": "TS3390442", "make": "Toshiba", "model": "e-STUDIO 5528A",
             "loc": "Pharmacy", "install": -190, "warranty": 905,
             "bw": 19600, "clr": 0, "duty": 30000, "contract": "C-0203",
             "lease": "L-0204", "calls": 1},
            {"id": "EQ-0208", "serial": "TS3390507", "make": "Toshiba", "model": "e-STUDIO 3515AC",
             "loc": "Outpatient reception", "install": -190, "warranty": 905,
             "bw": 10400, "clr": 6100, "duty": 22000, "contract": "C-0203",
             "lease": "L-0204", "calls": 0},
            {"id": "EQ-0209", "serial": "LX8810330", "make": "Lexmark", "model": "MX622adhe",
             "loc": "Lab annexe", "install": -1800, "warranty": -700,
             "bw": 5600, "clr": 0, "duty": 6000, "contract": None,
             "lease": None, "calls": 4},
            {"id": "EQ-0210", "serial": "LX8810384", "make": "Lexmark", "model": "CX625ade",
             "loc": "Physio", "install": -1800, "warranty": -700,
             "bw": 3200, "clr": 1800, "duty": 5000, "contract": None,
             "lease": None, "calls": 5},
        ],
        "leases": [
            {"id": "L-0201", "schedule": "CT-9910-A", "term": 60, "start": -1430, "end": 395,
             "payment": 1642.90, "financed": 84200.0, "principal": 18740.20,
             "factor": 0.01951, "rate": 7.1},
            {"id": "L-0202", "schedule": "CT-1188-A", "term": 63, "start": -560, "end": 1355,
             "payment": 2104.55, "financed": 118600.0, "principal": 86420.90,
             "factor": 0.01774, "rate": 6.4},
            {"id": "L-0203", "schedule": "CT-1188-B", "term": 60, "start": -540, "end": 1285,
             "payment": 486.20, "financed": 25100.0, "principal": 17980.40,
             "factor": 0.01937, "rate": 6.9},
            {"id": "L-0204", "schedule": "CT-2204-A", "term": 48, "start": -190, "end": 1270,
             "payment": 1188.75, "financed": 52100.0, "principal": 45310.60,
             "factor": 0.02281, "rate": 7.4},
        ],
    },
    {
        "num": "CUST-03", "name": "Fabrikam Legal Group", "city": "Hartford", "state": "CT",
        "domain": "fabrikamlegal.example",
        "story": "The downsize: four devices badly over-specced for what they print.",
        "contracts": [
            {"id": "C-0301", "type": "Full Service", "start": -880, "exp": 62,
             "rate": 1240.0, "period": "1", "renewable": True, "copies": 300000,
             "unearned": 2140.0},
        ],
        "devices": [
            {"id": "EQ-0301", "serial": "KY6620915", "make": "Kyocera", "model": "TASKalfa 7054ci",
             "loc": "Main copy centre", "install": -850, "warranty": 250,
             "bw": 6200, "clr": 1900, "duty": 70000, "contract": "C-0301",
             "lease": "L-0301", "calls": 1},
            {"id": "EQ-0302", "serial": "KY6620981", "make": "Kyocera", "model": "TASKalfa 6054ci",
             "loc": "Partners floor", "install": -850, "warranty": 250,
             "bw": 4100, "clr": 2200, "duty": 60000, "contract": "C-0301",
             "lease": "L-0301", "calls": 0},
            {"id": "EQ-0303", "serial": "KY6621044", "make": "Kyocera", "model": "TASKalfa 4054ci",
             "loc": "Paralegal pool", "install": -820, "warranty": 280,
             "bw": 5400, "clr": 800, "duty": 40000, "contract": "C-0301",
             "lease": "L-0302", "calls": 2},
            {"id": "EQ-0304", "serial": "KY6621100", "make": "Kyocera", "model": "ECOSYS MA4000cifx",
             "loc": "Records room", "install": -820, "warranty": 280,
             "bw": 1800, "clr": 400, "duty": 12000, "contract": "C-0301",
             "lease": "L-0302", "calls": 0},
        ],
        "leases": [
            {"id": "L-0301", "schedule": "FB-3320-A", "term": 60, "start": -850, "end": 975,
             "payment": 1289.40, "financed": 66800.0, "principal": 36190.85,
             "factor": 0.01930, "rate": 6.9},
            {"id": "L-0302", "schedule": "FB-3320-B", "term": 60, "start": -820, "end": 1005,
             "payment": 604.15, "financed": 31300.0, "principal": 17420.30,
             "factor": 0.01930, "rate": 6.9},
        ],
    },
]

CALL_NOTES = [
    "Paper jam, fuser area. Cleared and cleaned rollers.",
    "Streaking on colour output. Replaced drum unit.",
    "Won't pull from tray 3. Replaced pickup assembly.",
    "Error C-2557 on startup. Reseated developer unit.",
    "Toner sensor fault. Replaced sensor and recalibrated.",
    "Scanner ADF misfeeding. Replaced separation pad.",
    "Fuser life exceeded. Fuser replaced.",
    "Noise from main drive. Drive gear replaced.",
    "Waste toner full alarm not clearing. Reset and cleaned.",
]


def upsert(obj: str, id_prop: str, rows: list[dict], label: str) -> dict[str, str]:
    """batch/upsert on a unique property. Returns key -> record id.

    A 207 here means PARTIAL failure and is a success status, so the per-row errors are
    read rather than the response code trusted."""
    out: dict[str, str] = {}
    for i in range(0, len(rows), 100):
        chunk = rows[i:i + 100]
        r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/batch/upsert",
                 {"inputs": [{"idProperty": id_prop, "id": c["properties"][id_prop],
                              "properties": c["properties"]} for c in chunk]})
        if "__error" in r:
            print(f"  ! {label} batch {i//100}: {r['__error']} {r.get('__body','')[:300]}",
                  file=sys.stderr)
            continue
        for res in r.get("results", []):
            key = (res.get("properties") or {}).get(id_prop)
            if key:
                out[str(key)] = str(res["id"])
        for e in (r.get("errors") or []):
            print(f"  ! {label}: {str(e)[:220]}", file=sys.stderr)
    print(f"  {label}: {len(out)}/{len(rows)}", file=sys.stderr)
    return out


def find_by_prop(obj: str, prop: str, values: list[str]) -> dict[str, str]:
    """For objects whose key is not unique, so upsert is unavailable."""
    out: dict[str, str] = {}
    for i in range(0, len(values), 100):
        r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/search",
                 {"limit": 100, "properties": [prop],
                  "filterGroups": [{"filters": [
                      {"propertyName": prop, "operator": "IN",
                       "values": values[i:i + 100]}]}]})
        for res in r.get("results", []):
            v = (res.get("properties") or {}).get(prop)
            if v:
                out[str(v)] = str(res["id"])
    return out


def create_plain(obj: str, rows: list[dict], label: str) -> list[str]:
    ids = []
    for i in range(0, len(rows), 100):
        r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/batch/create",
                 {"inputs": rows[i:i + 100]})
        if "__error" in r:
            print(f"  ! {label} batch {i//100}: {r['__error']} {r.get('__body','')[:300]}",
                  file=sys.stderr)
            continue
        ids += [str(x["id"]) for x in r.get("results", [])]
    print(f"  {label}: {len(ids)}/{len(rows)} created", file=sys.stderr)
    return ids


def assoc_type(frm: str, to: str) -> int | None:
    r = call("GET", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                    f"{urllib.parse.quote(to)}/labels")
    if "__error" in r:
        return None
    for t in r.get("results", []):
        if t.get("label") is None:
            return t["typeId"]
    res = r.get("results", [])
    return res[0]["typeId"] if res else None


def link(frm: str, to: str, pairs: list[tuple[str, str]], label: str) -> None:
    if not pairs:
        return
    tid = assoc_type(frm, to)
    if tid is None:
        print(f"  {label}: SKIPPED, no association definition", file=sys.stderr)
        return
    made = 0
    for i in range(0, len(pairs), 100):
        r = call("POST", f"/crm/v4/associations/{urllib.parse.quote(frm)}/"
                         f"{urllib.parse.quote(to)}/batch/create",
                 {"inputs": [{"from": {"id": a}, "to": {"id": b},
                              "types": [{"associationCategory": "USER_DEFINED",
                                         "associationTypeId": tid}]} for a, b in pairs[i:i + 100]]})
        if "__error" in r:
            print(f"  ! {label}: {r['__error']} {r.get('__body','')[:200]}", file=sys.stderr)
            continue
        made += len(r.get("results", []))
    print(f"  {label}: {made}/{len(pairs)} edges", file=sys.stderr)


def delete_demo() -> None:
    """Remove exactly the DEMO- prefixed records."""
    targets = [
        (COMPANY, "ea_customer_number"), (EQUIPMENT, "ea_equipment_number"),
        (CONTRACT, "ea_contract_number"), (LEASE, "ea_contract_detail_id"),
        (METER, "ea_meter_key"), (SERVICE_CALL, "ea_call_number"),
    ]
    for obj, prop in targets:
        ids, after = [], None
        while True:
            payload = {"limit": 100, "properties": [prop],
                       "filterGroups": [{"filters": [
                           {"propertyName": prop, "operator": "CONTAINS_TOKEN",
                            "value": f"{PREFIX}*"}]}]}
            if after:
                payload["after"] = after
            r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/search", payload)
            if "__error" in r:
                print(f"  ! search {obj}: {r['__error']} {r.get('__body','')[:200]}",
                      file=sys.stderr)
                break
            for res in r.get("results", []):
                v = str((res.get("properties") or {}).get(prop) or "")
                if v.startswith(PREFIX):
                    ids.append(str(res["id"]))
            after = (r.get("paging") or {}).get("next", {}).get("after")
            if not after:
                break
        for i in range(0, len(ids), 100):
            call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/batch/archive",
                 {"inputs": [{"id": x} for x in ids[i:i + 100]]})
        print(f"  {obj}: archived {len(ids)}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--delete", action="store_true")
    args = ap.parse_args()

    if args.delete:
        print("archiving DEMO- records ...", file=sys.stderr)
        delete_demo()
        return

    # ── plan summary ────────────────────────────────────────────────────────
    print(f"{'account':26} {'dev':>4} {'ctr':>4} {'lse':>4} {'mtr':>4} {'call':>5} "
          f"{'pages/mo':>10} {'spend/mo':>9}", file=sys.stderr)
    for a in ACCOUNTS:
        vol = sum(x["bw"] + x["clr"] for x in a["devices"])
        spend = sum(c["rate"] for c in a["contracts"]) + \
            sum(l["payment"] for l in a["leases"])
        meters = sum(2 if x["clr"] else 1 for x in a["devices"]) + len(a["devices"])
        print(f"{a['name'][:26]:26} {len(a['devices']):4} {len(a['contracts']):4} "
              f"{len(a['leases']):4} {meters:4} {sum(x['calls'] for x in a['devices']):5} "
              f"{vol:10,} {spend:9,.0f}", file=sys.stderr)
        print(f"{'':26} {a['story']}", file=sys.stderr)

    if not args.apply:
        print("\n--plan only. Re-run with --apply.", file=sys.stderr)
        return

    print("\ncompanies ...", file=sys.stderr)
    co_rows = [{"properties": {
        "name": a["name"], "ea_customer_number": PREFIX + a["num"],
        "city": a["city"], "state": a["state"], "domain": a["domain"],
        "ea_prospect": "false",
    }} for a in ACCOUNTS]
    co_ids = upsert(COMPANY, "ea_customer_number", co_rows, "Company")

    print("contracts ...", file=sys.stderr)
    # THE ALLOWANCE MUST RECONCILE WITH THE DEVICES ON THE CONTRACT, AND SIT BELOW THEM.
    #
    # ea_exp_copies shares the base rate's period -- verified against this portal's real
    # e-automate contracts, which pair 10,000 copies with a $200 MONTHLY base rate. The
    # first version of this fixture set a flat 240,000 against devices running 57,000: an
    # allowance four times actual, which taught the exact opposite of the intended lesson,
    # because the screen then read "well within allowance" on a fleet built to demonstrate
    # overage exposure.
    #
    # Derived per contract from its OWN devices instead, deliberately under actual so every
    # agreement shows overage -- which is the point of the comparison. The factor varies by
    # account so the three read differently: Contoso is badly under-contracted, Northwind
    # modestly, Fabrikam barely.
    UNDER = {"CUST-01": 0.92, "CUST-02": 0.78, "CUST-03": 0.95}
    allowance: dict[str, int] = {}
    for a in ACCOUNTS:
        f = UNDER.get(a["num"], 0.9)
        for c in a["contracts"]:
            actual = sum(x["bw"] + x["clr"] for x in a["devices"]
                         if x["contract"] == c["id"])
            allowance[c["id"]] = int(round(actual * f / 100.0) * 100) if actual else 0
    ct_rows = []
    for a in ACCOUNTS:
        for c in a["contracts"]:
            ct_rows.append({"properties": {
                "ea_contract_number": PREFIX + c["id"],
                # BOTH required by this portal's Contract object; omitting either 400s
                # the entire batch rather than the row.
                "contractnumber": PREFIX + c["id"],
                "contract_type": c["type"],
                "start_date": d(c["start"]), "ea_exp_date": d(c["exp"]),
                "ea_renewable": "true" if c["renewable"] else "false",
                "base_rate": str(c["rate"]), "ea_base_rate_period": c["period"],
                "ea_exp_copies": str(allowance.get(c["id"]) or c["copies"]),
                "ea_unearned_balance": str(c["unearned"]),
                # NOT ea_customer_number: neither Contract nor Equipment has that
                # property in this portal. The Company association carries the
                # relationship, which is the correct model anyway -- a customer number
                # duplicated onto a child is a second source of truth for the same edge.
            }})
    ct_ids = upsert(CONTRACT, "ea_contract_number", ct_rows, "Contract")

    print("equipment ...", file=sys.stderr)
    eq_rows = []
    for a in ACCOUNTS:
        for x in a["devices"]:
            eq_rows.append({"properties": {
                "ea_equipment_number": PREFIX + x["id"],
                "ea_serial_number": x["serial"],
                "make": x["make"], "model": x["model"],
                "ea_location_description": x["loc"],
                "ea_city": a["city"], "ea_state": a["state"],
                "install_date": d(x["install"]),
                "ea_warranty_date": d(x["warranty"]),
                "active": "true",
            }})
    eq_ids = upsert(EQUIPMENT, "ea_equipment_number", eq_rows, "Equipment")

    print("leases ...", file=sys.stderr)
    ls_rows = []
    for a in ACCOUNTS:
        for l in a["leases"]:
            ls_rows.append({"properties": {
                "ea_contract_detail_id": PREFIX + l["id"],
                "ea_contract_number": PREFIX + a["contracts"][0]["id"],
                "ea_lease_schedule": l["schedule"],
                "ea_lease_term": str(l["term"]),
                "ea_lease_payment_amount": str(l["payment"]),
                "ea_lease_financed_amount": str(l["financed"]),
                "ea_lease_principal_balance": str(l["principal"]),
                "ea_lease_rate_factor": str(l["factor"]),
                "ea_lease_interest_rate": str(l["rate"]),
                "ea_lease_payment_start_date": d(l["start"]),
                "ea_lease_payment_end_date": d(l["end"]),
                "ea_customer_number": PREFIX + a["num"],
            }})
    ls_ids = upsert(LEASE, "ea_contract_detail_id", ls_rows, "Lease")
    if len(ls_ids) < len(ls_rows):
        # ea_contract_detail_id may not be unique on a pre-existing Lease object, so
        # upsert can fall through. Create then look up by the same key.
        missing = [r for r in ls_rows
                   if r["properties"]["ea_contract_detail_id"] not in ls_ids]
        if missing:
            create_plain(LEASE, missing, "Lease (create fallback)")
            ls_ids |= find_by_prop(LEASE, "ea_contract_detail_id",
                                   [r["properties"]["ea_contract_detail_id"] for r in missing])

    print("meters ...", file=sys.stderr)
    me_rows = []
    for a in ACCOUNTS:
        for x in a["devices"]:
            total = x["bw"] + x["clr"]
            kinds = [("B\\W", x["bw"]), ("Total Count", total)]
            if x["clr"]:
                kinds.insert(1, ("Color", x["clr"]))
            for code, vol in kinds:
                me_rows.append({"properties": {
                    # Required by the Meter object, and the composite identity that no
                    # single CEO Juice field carries.
                    "ea_meter_key": f"{PREFIX}{x['id']}|{code}",
                    "ea_meter_type_code": code,
                    "ea_equipment_number": PREFIX + x["id"],
                    "ea_serial_number": x["serial"],
                    "ea_customer_number": PREFIX + a["num"],
                    "ea_is_default": "true" if code == "Total Count" else "false",
                    "ea_meter_digits": "7",
                    "ea_avg_monthly_volume12_mo": str(vol),
                    "ea_avg_monthly_volume6_mo": str(int(vol * 1.04)),
                    "ea_avg_monthly_volume3_mo": str(int(vol * 1.07)),
                    "ea_avg_monthly_volume_install": str(int(vol * 0.93)),
                    # The duty cycle only belongs on the machine total; a per-colour
                    # rating would imply the manufacturer publishes one, which it does not.
                    "ea_mfg_suggested_monthly_volume": str(x["duty"] if code == "Total Count" else 0),
                    "ea_target_monthly_volume": str(int(x["duty"] * 0.75) if code == "Total Count" else 0),
                }})
    me_ids = upsert(METER, "ea_meter_key", me_rows, "Meter")

    print("service calls ...", file=sys.stderr)
    sc_rows, sc_owner = [], []
    n = 0
    for a in ACCOUNTS:
        for x in a["devices"]:
            for k in range(x["calls"]):
                n += 1
                opened = -20 - (k * 47) - (n % 11) * 9
                closed = opened + 1 + (n % 4)
                still_open = k == 0 and x["calls"] >= 3
                sc_rows.append({"properties": {
                    "ea_call_number": f"{PREFIX}SC-{n:04d}",
                    "ea_status": "O" if still_open else "C",
                    "ea_date": d(opened),
                    "ea_close_date": "" if still_open else d(min(closed, -1)),
                    "ea_description": CALL_NOTES[n % len(CALL_NOTES)],
                    "ea_equipment_number": PREFIX + x["id"],
                    "ea_serial_number": x["serial"],
                    "ea_customer_number": PREFIX + a["num"],
                    "ea_address_city": a["city"], "ea_address_state": a["state"],
                }})
                sc_owner.append((f"{PREFIX}SC-{n:04d}", PREFIX + x["id"], PREFIX + a["num"]))
    sc_ids = upsert(SERVICE_CALL, "ea_call_number", sc_rows, "Service Call")

    # ── associations ────────────────────────────────────────────────────────
    print("\nassociations ...", file=sys.stderr)
    co_eq, co_ct, co_ls, co_me, co_sc = [], [], [], [], []
    eq_ct, eq_ls, eq_me, eq_sc, ct_ls = [], [], [], [], []

    for a in ACCOUNTS:
        cid = co_ids.get(PREFIX + a["num"])
        if not cid:
            print(f"  ! no company id for {a['num']}", file=sys.stderr)
            continue
        for c in a["contracts"]:
            x = ct_ids.get(PREFIX + c["id"])
            if x:
                co_ct.append((cid, x))
        for l in a["leases"]:
            x = ls_ids.get(PREFIX + l["id"])
            if x:
                co_ls.append((cid, x))
                first = ct_ids.get(PREFIX + a["contracts"][0]["id"])
                if first:
                    ct_ls.append((first, x))
        for dv in a["devices"]:
            e = eq_ids.get(PREFIX + dv["id"])
            if not e:
                continue
            co_eq.append((cid, e))
            if dv["contract"]:
                x = ct_ids.get(PREFIX + dv["contract"])
                if x:
                    eq_ct.append((e, x))
            if dv["lease"]:
                x = ls_ids.get(PREFIX + dv["lease"])
                if x:
                    eq_ls.append((e, x))
            for code in ("B\\W", "Color", "Total Count"):
                m = me_ids.get(f"{PREFIX}{dv['id']}|{code}")
                if m:
                    eq_me.append((e, m))
                    co_me.append((cid, m))
    for callno, eqno, custno in sc_owner:
        s = sc_ids.get(callno)
        e = eq_ids.get(eqno)
        c = co_ids.get(custno)
        if s and e:
            eq_sc.append((e, s))
        if s and c:
            co_sc.append((c, s))

    link(COMPANY, EQUIPMENT, co_eq, "Company -> Equipment")
    link(COMPANY, CONTRACT, co_ct, "Company -> Contract")
    link(COMPANY, LEASE, co_ls, "Company -> Lease")
    link(COMPANY, METER, co_me, "Company -> Meter")
    link(COMPANY, SERVICE_CALL, co_sc, "Company -> Service Call")
    link(EQUIPMENT, CONTRACT, eq_ct, "Equipment -> Contract")
    link(EQUIPMENT, LEASE, eq_ls, "Equipment -> Lease")
    link(EQUIPMENT, METER, eq_me, "Equipment -> Meter")
    link(EQUIPMENT, SERVICE_CALL, eq_sc, "Equipment -> Service Call")
    link(CONTRACT, LEASE, ct_ls, "Contract -> Lease")

    # ── equipment rollups ───────────────────────────────────────────────────
    # Equipment carries its own restatement of the meter figures. Written here from the
    # fixture so they AGREE with the meters, because a generator that authors them
    # independently produces a device whose mono plus colour does not equal its total --
    # which is what happened on the first fill pass and reads as a broken screen.
    print("\nequipment rollups ...", file=sys.stderr)
    eq_roll = []
    for a in ACCOUNTS:
        for x in a["devices"]:
            eid = eq_ids.get(PREFIX + x["id"])
            if not eid:
                continue
            total = x["bw"] + x["clr"]
            eq_roll.append({"id": eid, "properties": {
                "ea_bw_avg_monthly_volume12_mo": str(x["bw"]),
                "ea_color_avg_monthly_volume12_mo": str(x["clr"]),
                "ea_total_avg_monthly_volume12_mo": str(total),
                "ea_meter_count": str((2 if x["clr"] else 1) + 1),
                "ea_is_metered": "true",
            }})
    for i in range(0, len(eq_roll), 100):
        r = call("POST", f"/crm/v3/objects/{EQUIPMENT}/batch/update",
                 {"inputs": eq_roll[i:i + 100]})
        if "__error" in r:
            print(f"  ! equipment rollups: {r['__error']} {r.get('__body','')[:200]}",
                  file=sys.stderr)
    print(f"  {len(eq_roll)} devices rolled up", file=sys.stderr)

    # ── company rollups ─────────────────────────────────────────────────────
    # The real accounts get these from PrintReleaf, which knows nothing about DEMO-
    # customers. Computed from the fixture's own meters instead, and marked
    # basis=actual_12mo because that is genuinely what these values represent here: a
    # per-meter twelve-month average, which is exactly what the sandbox lacks.
    print("\ncompany rollups ...", file=sys.stderr)
    roll = []
    for a in ACCOUNTS:
        cid = co_ids.get(PREFIX + a["num"])
        if not cid:
            continue
        bw = sum(x["bw"] for x in a["devices"])
        clr = sum(x["clr"] for x in a["devices"])
        total = bw + clr
        meters = sum((2 if x["clr"] else 1) + 1 for x in a["devices"])
        expiries = sorted(d(c["exp"]) for c in a["contracts"])
        # Lifetime approximated from each device's own age at its own rate, rather than
        # one fleet figure times one duration -- the machines were installed at different
        # times and a single multiplier would overstate the newest ones.
        lifetime = sum(int((x["bw"] + x["clr"]) * (abs(x["install"]) / 30.44))
                       for x in a["devices"])
        spend = sum(c["rate"] for c in a["contracts"]) + \
            sum(l["payment"] for l in a["leases"])
        roll.append({"id": cid, "properties": {
            "ea_fleet_machine_count": str(len(a["devices"])),
            "ea_fleet_meter_count": str(meters),
            "ea_fleet_monthly_volume": str(total),
            "ea_fleet_volume_basis": "actual_12mo",
            "ea_fleet_volume_period": "trailing 12 months",
            "ea_fleet_color_pct": str(round(100.0 * clr / total, 1) if total else 0),
            "ea_fleet_lifetime_pages": str(lifetime),
            "ea_fleet_contract_count": str(len(a["contracts"])),
            "ea_fleet_lease_count": str(len(a["leases"])),
            "ea_fleet_open_calls": str(sum(1 for x in a["devices"] if x["calls"] >= 3)),
            "ea_fleet_next_expiry": expiries[0] if expiries else "",
            "ea_fleet_monthly_spend": str(round(spend, 2)),
            "ea_fleet_summary_updated": TODAY.isoformat(),
        }})
    r = call("POST", f"/crm/v3/objects/{COMPANY}/batch/update", {"inputs": roll})
    if "__error" in r:
        print(f"  ! rollups: {r['__error']} {r.get('__body','')[:300]}", file=sys.stderr)
    else:
        print(f"  {len(r.get('results', []))}/{len(roll)} companies rolled up",
              file=sys.stderr)

    print("\nVERIFY (read back per company)", file=sys.stderr)
    for a in ACCOUNTS:
        cid = co_ids.get(PREFIX + a["num"])
        if not cid:
            continue
        counts = {}
        for lab, oid in (("dev", EQUIPMENT), ("ctr", CONTRACT), ("lse", LEASE),
                         ("mtr", METER), ("call", SERVICE_CALL)):
            r = call("GET", f"/crm/v4/objects/companies/{cid}/associations/"
                            f"{urllib.parse.quote(oid)}?limit=200")
            counts[lab] = len(r.get("results", [])) if "__error" not in r else "ERR"
        print(f"  {a['name'][:26]:26} id {cid}  {counts}", file=sys.stderr)


if __name__ == "__main__":
    main()
