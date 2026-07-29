#!/usr/bin/env python3
"""Provision a HubSpot portal for the CEO Juice / e-automate integration.

One command per client. Creates the custom objects, the e-Automate property group,
the properties and the unique match keys, then optionally loads a sample of real
e-automate records so somebody can see it worked.

    export HUBSPOT_TOKEN=pat-na1-...          # target portal
    export CEOJUICE_USERNAME=... CEOJUICE_PASSWORD=...

    python scripts/provision_hubspot.py --plan          # show, change nothing
    python scripts/provision_hubspot.py --apply         # objects + properties
    python scripts/provision_hubspot.py --apply --load  # ...and sample data

IDEMPOTENT. Every step checks for what already exists first, so a re-run against a
half-provisioned portal finishes the job rather than erroring or duplicating. That
matters because provisioning genuinely does fail partway — HubSpot returned a 502 on
one property create and a read timeout on a delete during the first live run.

WHAT THIS DELIBERATELY DOES NOT DO
  - Lookup resolution. 18 e-automate fields point at code tables; they should sync as
    the label ("Net 10"), not the id (1), which needs the lookup fetched first.
  - Phase 2. 381 further properties are specified and deliberately not created:
    two dozen e-automate columns on a deal buries the handful a rep reads.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"

# ---------------------------------------------------------------------------
# Custom objects to create. Standard objects are used wherever possible because
# they cost nothing against the portal's custom-object budget: Customer->Company,
# SalesOrder->Deal, Item->Product, order/invoice lines->line_items.
#
# Service calls get their own object rather than Tickets. Measured reason: a real
# portal already runs several ticket pipelines for the agency's own business (five in
# the demo portal), and a dealer's call volume — thousands a month against 225 in the
# sandbox — would swamp them and pollute every existing ticket report.
#
# Meters get their own object because 69% of machines carry more than one (up to six,
# across eight types: B\W, Color, Total Count, Print, Scanner, Fax, Copy, Virtual).
# Flattened onto Equipment, one machine's three meters share one set of columns and
# whichever syncs last wins — a number that looks authoritative and is the wrong
# meter. Equipment instead gets type-qualified rollups for filtering.
# ---------------------------------------------------------------------------
CUSTOM_OBJECTS = [
    {
        "name": "ea_service_call",
        "labels": {"singular": "e-Auto Service Call", "plural": "e-Auto Service Calls"},
        "key": "ea_call_number",
        "key_label": "e-automate Call Number",
        "why": "Service call from e-automate (CEO Juice ID136).",
    },
    {
        "name": "ea_meter",
        "labels": {"singular": "e-Auto Meter", "plural": "e-Auto Meters"},
        "key": "ea_meter_key",
        "key_label": "e-automate Meter Key",
        "why": "One record per machine per meter: <equipmentNumber>|<meterTypeCode>.",
    },
    {
        "name": "ea_invoice",
        "labels": {"singular": "e-Auto Invoice", "plural": "e-Auto Invoices"},
        "key": "ea_invoice_number",
        "key_label": "e-automate Invoice Number",
        "why": "Billing history from e-automate.",
    },
]

# Object type -> (match key property, source field). The match key carries
# hasUniqueValue, which is why each was verified distinct with no blanks in live data
# before being trusted:
#   customerNumber 160/160 · equipmentNumber 600/600 · contractNumber 400/400
#   soNumber 400/400 · callNumber 226/226
# serialNumber is NOT used for Equipment despite being the intuitive choice and what
# the generated spec proposes: 35 duplicated values and 8 blanks across 600 records.
# HubSpot rejects a second record on a unique property rather than degrading, so a key
# with duplicates kills the sync on first collision. It also cannot be corrected later
# — PATCHing hasUniqueValue onto an existing property returns 200 and silently leaves
# it false.
MATCH_KEYS = {
    "companies": ("ea_customer_number", "customerNumber", "e-automate Customer Number"),
    "deals": ("ea_so_number", "soNumber", "e-automate Sales Order Number"),
    "$equipment": ("ea_equipment_number", "equipmentNumber", "e-automate Equipment Number"),
    "$contract": ("ea_contract_number", "contractNumber", "e-automate Contract Number"),
}

GROUP = {"name": "e_automate", "label": "e-Automate (CEO Juice)", "displayOrder": -1}

S = lambda n, l, d="": {"name": n, "label": l, "type": "string", "fieldType": "text",
                        "groupName": GROUP["name"], "description": d}
N = lambda n, l, d="": {"name": n, "label": l, "type": "number", "fieldType": "number",
                        "groupName": GROUP["name"], "description": d}
D = lambda n, l, d="": {"name": n, "label": l, "type": "date", "fieldType": "date",
                        "groupName": GROUP["name"], "description": d}
B = lambda n, l, d="": {"name": n, "label": l, "type": "enumeration",
                        "fieldType": "booleancheckbox", "groupName": GROUP["name"],
                        "description": d,
                        "options": [{"label": "Yes", "value": "true", "displayOrder": 0},
                                    {"label": "No", "value": "false", "displayOrder": 1}]}

SERVICE_CALL_PROPS = [
    S("ea_status", "e-auto Status"), S("ea_description", "e-auto Description"),
    D("ea_date", "e-auto Call Date"), D("ea_close_date", "e-auto Close Date"),
    D("ea_req_date", "e-auto Requested Date"), S("ea_caller", "e-auto Caller"),
    S("ea_equipment_number", "e-auto Equipment Number", "Which machine the call is against."),
    S("ea_serial_number", "e-auto Serial Number"),
    S("ea_customer_number", "e-auto Customer Number", "Parent account. Association key."),
    S("ea_address_city", "e-auto City"), S("ea_address_state", "e-auto State"),
    S("ea_reference_call_identifier", "e-auto Reference Call Id",
      "Our own ticket id, so a call can be reconciled back."),
    N("ea_call_id", "e-auto Call Id", "Surrogate PK. Tie-break anchor only."),
]

METER_PROPS = [
    S("ea_equipment_number", "e-auto Equipment Number", "The machine this meter belongs to."),
    S("ea_serial_number", "e-auto Serial Number"),
    S("ea_customer_number", "e-auto Customer Number"),
    S("ea_meter_type_code", "e-auto Meter Type",
      "B\\W, Color, Total Count, Print, Scanner, Fax, Copy or Virtual."),
    N("ea_avg_monthly_volume3_mo", "e-auto Avg Monthly Volume 3mo",
      "Computed by e-automate. Reads 0 where no reading history exists, and there is no "
      "reading-history route to recompute from — treat 0 as UNKNOWN, never as no printing."),
    N("ea_avg_monthly_volume6_mo", "e-auto Avg Monthly Volume 6mo"),
    N("ea_avg_monthly_volume12_mo", "e-auto Avg Monthly Volume 12mo"),
    N("ea_avg_monthly_volume_install", "e-auto Avg Monthly Volume since Install"),
    N("ea_mfg_suggested_monthly_volume", "e-auto Mfg Suggested Monthly Volume",
      "Manufacturer rated duty cycle. Populated where the rolling averages are not, so "
      "this plus target is what a fleet can actually be sized from today."),
    N("ea_target_monthly_volume", "e-auto Target Monthly Volume"),
    N("ea_meter_digits", "e-auto Meter Digits"),
    B("ea_is_default", "e-auto Is Default Meter"),
]

# Rollups on Equipment. Detail lives on the Meter object; these exist because a rep
# filters on Equipment, not on a child record.
EQUIPMENT_ROLLUPS = [
    N("ea_bw_avg_monthly_volume12_mo", "e-auto B/W Avg Monthly Volume 12mo",
      "Rollup of the B\\W meter. Detail on e-Auto Meter."),
    N("ea_color_avg_monthly_volume12_mo", "e-auto Color Avg Monthly Volume 12mo"),
    N("ea_total_avg_monthly_volume12_mo", "e-auto Total Avg Monthly Volume 12mo"),
    N("ea_meter_count", "e-auto Meter Count", "How many meters this machine carries."),
]

EQUIPMENT_PROPS = [
    S("ea_serial_number", "e-auto Serial Number",
      "Stored and searchable, but NOT the match key — 35 duplicated values and 8 blanks "
      "across 600 records."),
    S("ea_city", "e-auto City"), S("ea_state", "e-auto State"), S("ea_zip", "e-auto Zip"),
    S("ea_address", "e-auto Address"), S("ea_description", "e-auto Description"),
    S("ea_location_description", "e-auto Location"), S("ea_contact", "e-auto Contact"),
    S("ea_contact_phone", "e-auto Contact Phone"),
    S("ea_decision_maker", "e-auto Decision Maker"),
    S("ea_decision_maker_phone", "e-auto Decision Maker Phone"),
    D("ea_warranty_date", "e-auto Warranty Date"),
    N("ea_warranty_meter", "e-auto Warranty Meter"), N("ea_pm_meter_due", "e-auto PM Meter Due"),
]


class HubSpot:
    def __init__(self, token: str, dry: bool = False):
        self.token = token
        self.dry = dry

    def call(self, method: str, path: str, body=None, tries: int = 4):
        if self.dry and method != "GET":
            print(f"    [plan] {method} {path}")
            return 0, {}
        data = json.dumps(body).encode() if body is not None else None
        last = None
        for attempt in range(tries):
            req = urllib.request.Request(
                API + path, data=data, method=method,
                headers={"Authorization": f"Bearer {self.token}",
                         "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read()
                    return resp.status, (json.loads(raw) if raw.strip() else {})
            except urllib.error.HTTPError as exc:
                raw = exc.read()
                try:
                    parsed = json.loads(raw or b"{}")
                except Exception:
                    parsed = {}
                # 409 = already exists, which is success for an idempotent provisioner.
                if exc.code == 409:
                    return exc.code, parsed
                if exc.code >= 500 and attempt < tries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return exc.code, parsed
            except Exception as exc:  # read timeout mid-write is common here
                last = exc
                if attempt < tries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError(str(last))

    def schemas(self) -> dict[str, str]:
        _, d = self.call("GET", "/crm/v3/schemas")
        return {s["name"]: s["objectTypeId"] for s in d.get("results", [])}

    def properties(self, ot: str) -> set[str]:
        s, d = self.call("GET", f"/crm/v3/properties/{ot}")
        return {p["name"] for p in d.get("results", [])} if s == 200 else set()

    def ensure_group(self, ot: str) -> None:
        self.call("POST", f"/crm/v3/properties/{ot}/groups", GROUP)

    def ensure_properties(self, ot: str, props: list[dict], label: str) -> int:
        have = self.properties(ot)
        todo = [p for p in props if p["name"] not in have]
        if not todo:
            print(f"    {label}: all {len(props)} present")
            return 0
        made = 0
        for i in range(0, len(todo), 50):
            s, r = self.call("POST", f"/crm/v3/properties/{ot}/batch/create",
                             {"inputs": todo[i:i + 50]})
            made += len(r.get("results", []))
            if s not in (200, 201):
                print(f"    ! {label} batch HTTP {s} {str(r.get('message'))[:120]}")
        print(f"    {label}: created {made}, {len(have & {p['name'] for p in props})} already there")
        return made

    def ensure_match_key(self, ot: str, name: str, label: str) -> None:
        if name in self.properties(ot):
            print(f"    key {name}: exists")
            return
        s, d = self.call("POST", f"/crm/v3/properties/{ot}", {
            "name": name, "label": label, "type": "string", "fieldType": "text",
            "groupName": GROUP["name"], "hasUniqueValue": True,
            "description": "e-automate match key. Verified distinct with no blanks in "
                           "source data. hasUniqueValue cannot be added later — a PATCH "
                           "returns 200 and silently leaves it false."})
        print(f"    key {name}: HTTP {s} unique={d.get('hasUniqueValue')}")

    def regroup(self, ot: str) -> int:
        s, d = self.call("GET", f"/crm/v3/properties/{ot}")
        moved = 0
        for p in d.get("results", []):
            if p["name"].startswith("ea_") and p.get("groupName") != GROUP["name"]:
                st, _ = self.call("PATCH", f"/crm/v3/properties/{ot}/{p['name']}",
                                  {"groupName": GROUP["name"]})
                moved += st == 200
        return moved


def provision(hs: HubSpot) -> dict[str, str]:
    print("\n== custom objects ==")
    have = hs.schemas()
    ids: dict[str, str] = {}
    for spec in CUSTOM_OBJECTS:
        if spec["name"] in have:
            ids[spec["name"]] = have[spec["name"]]
            print(f"    {spec['labels']['singular']}: exists ({have[spec['name']]})")
            continue
        s, d = hs.call("POST", "/crm/v3/schemas", {
            "name": spec["name"], "labels": spec["labels"],
            "primaryDisplayProperty": spec["key"],
            "requiredProperties": [spec["key"]],
            "searchableProperties": [spec["key"]],
            "properties": [{"name": spec["key"], "label": spec["key_label"],
                            "type": "string", "fieldType": "text",
                            "hasUniqueValue": True, "description": spec["why"]}],
            "associatedObjects": ["COMPANY"]})
        oid = d.get("objectTypeId")
        if oid:
            ids[spec["name"]] = oid
        print(f"    {spec['labels']['singular']}: HTTP {s} id={oid} "
              f"{str(d.get('message', ''))[:80]}")

    # Equipment and Contract are commonly already present in an agency portal under
    # their own names; resolve rather than assume.
    have = hs.schemas()
    eq = have.get("equipment")
    ct = have.get("contract")
    print(f"\n    resolved existing: equipment={eq} contract={ct}")

    targets = {"companies": None, "contacts": None, "deals": None, "tickets": None,
               "products": None, "line_items": None}
    for k, v in ids.items():
        targets[v] = None
    if eq:
        targets[eq] = None
    if ct:
        targets[ct] = None

    print("\n== property groups ==")
    for ot in targets:
        hs.ensure_group(ot)
    print(f"    e_automate group ensured on {len(targets)} objects")

    print("\n== match keys (hasUniqueValue) ==")
    for ot, (name, _src, label) in MATCH_KEYS.items():
        real = {"$equipment": eq, "$contract": ct}.get(ot, ot)
        if not real:
            print(f"    {name}: skipped — target object not in this portal")
            continue
        hs.ensure_match_key(real, name, label)
    for spec in CUSTOM_OBJECTS:  # their keys are created with the schema
        if spec["name"] in ids:
            print(f"    key {spec['key']}: created with {spec['labels']['singular']}")

    print("\n== properties ==")
    if eq:
        hs.ensure_properties(eq, EQUIPMENT_PROPS + EQUIPMENT_ROLLUPS, "Equipment")
    if "ea_service_call" in ids:
        hs.ensure_properties(ids["ea_service_call"], SERVICE_CALL_PROPS, "Service Call")
    if "ea_meter" in ids:
        hs.ensure_properties(ids["ea_meter"], METER_PROPS, "Meter")

    print("\n== tidy: move stray ea_ properties into the group ==")
    for ot in targets:
        n = hs.regroup(ot)
        if n:
            print(f"    {ot}: moved {n}")

    return {"equipment": eq, "contract": ct, **ids}


def load_sample(hs: HubSpot, ids: dict, limit: int = 25) -> None:
    """Load a slice of real e-automate records so the wiring is visibly working."""
    sys.path.insert(0, os.getcwd())
    from ceojuice import CeoJuiceClient, CeoJuiceError

    cj = CeoJuiceClient()
    seg = lambda v: urllib.parse.quote(str(v), safe="")
    day = lambda v: (str(v)[:10] if v else None)

    print("\n== sample data ==")
    custs = list(itertools.islice(cj.customers(page_size=100), limit))
    by_id = {c["customerId"]: c["customerNumber"] for c in custs}
    hs.call("POST", "/crm/v3/objects/companies/batch/upsert", {"inputs": [
        {"idProperty": "ea_customer_number", "id": c["customerNumber"],
         "properties": {"ea_customer_number": c["customerNumber"], "name": c["customerName"],
                        "city": c.get("city") or "", "state": c.get("state") or "",
                        "phone": c.get("phone1") or ""}} for c in custs]})
    print(f"    companies: {len(custs)}")

    if ids.get("equipment"):
        eqs = [e for e in itertools.islice(cj.active_equipment(page_size=100), 400)
               if e.get("customerId") in by_id][:40]
        hs.call("POST", f"/crm/v3/objects/{ids['equipment']}/batch/upsert", {"inputs": [
            {"idProperty": "ea_equipment_number", "id": e["equipmentNumber"],
             "properties": {"ea_equipment_number": e["equipmentNumber"],
                            "ea_serial_number": e.get("serialNumber") or "",
                            "ea_city": e.get("city") or "", "ea_state": e.get("state") or "",
                            "ea_description": e.get("locationDescription") or "",
                            "ea_contact": e.get("contact") or ""}} for e in eqs]})
        print(f"    equipment: {len(eqs)}")

        if ids.get("ea_meter"):
            rows, seen = [], set()
            for e in eqs:
                if not e.get("isMetered"):
                    continue
                try:
                    meters = cj.get(
                        f"/api/MeterReadings/EquipmentMetersByEqNo/{seg(e['equipmentNumber'])}") or []
                except CeoJuiceError:
                    continue
                for mt in meters:
                    code = (mt.get("meterType") or {}).get("meterTypeCode", "?")
                    key = f"{e['equipmentNumber']}|{code}"
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({"idProperty": "ea_meter_key", "id": key, "properties": {
                        "ea_meter_key": key, "ea_equipment_number": e["equipmentNumber"],
                        "ea_serial_number": e.get("serialNumber") or "",
                        "ea_customer_number": by_id.get(e.get("customerId")) or "",
                        "ea_meter_type_code": code,
                        "ea_avg_monthly_volume12_mo": mt.get("avgMonthlyVolume12Mo") or 0,
                        "ea_mfg_suggested_monthly_volume": mt.get("mfgSuggestedMonthlyVolume") or 0,
                        "ea_target_monthly_volume": mt.get("targetMonthlyVolume") or 0,
                        "ea_meter_digits": mt.get("meterDigits") or 0,
                        "ea_is_default": "true" if mt.get("isDefault") else "false"}})
            for i in range(0, len(rows), 100):
                hs.call("POST", f"/crm/v3/objects/{ids['ea_meter']}/batch/upsert",
                        {"inputs": rows[i:i + 100]})
            print(f"    meters: {len(rows)}")

    if ids.get("ea_service_call"):
        calls = list(itertools.islice(cj.open_service_calls(page_size=100), 40))
        hs.call("POST", f"/crm/v3/objects/{ids['ea_service_call']}/batch/upsert", {"inputs": [
            {"idProperty": "ea_call_number", "id": str(c["callNumber"]).strip(),
             "properties": {"ea_call_number": str(c["callNumber"]).strip(),
                            "ea_status": (c.get("status") or "").strip(),
                            "ea_description": (c.get("description") or "")[:400],
                            "ea_date": day(c.get("date")), "ea_close_date": day(c.get("closeDate")),
                            "ea_caller": (c.get("caller") or "")[:200],
                            "ea_address_city": c.get("addressCity") or "",
                            "ea_address_state": c.get("addressState") or "",
                            "ea_call_id": c.get("callId") or 0}} for c in calls]})
        print(f"    service calls: {len(calls)}")


def wire_associations(hs: HubSpot, ids: dict) -> None:
    """Link the records to each other.

    WHY THIS IS NOT OPTIONAL. Loading the objects without this leaves every record an
    orphan: forty pieces of equipment that belong to nobody, meters attached to no
    machine. The data is present and useless — a company record shows none of it, which
    is the one view that makes the integration look like it worked.

    The edges come from e-automate's own foreign keys, which is exactly the point made
    elsewhere about `customerId` being a relationship rather than a column: read as an
    integer it is a dead number, read as an edge it is the Equipment→Company link.

    Association type ids are DISCOVERED, never hardcoded. They differ per portal, and
    an existing Equipment object may already carry labelled variants (this portal had
    'Customer', 'Company' and 'Location' alongside the unlabelled default). The
    unlabelled type is used because it is the plain association; a labelled one may
    carry meaning in the portal's existing setup that we would be borrowing wrongly.
    """
    sys.path.insert(0, os.getcwd())
    from ceojuice import CeoJuiceClient, CeoJuiceError

    cj = CeoJuiceClient()
    seg = lambda v: urllib.parse.quote(str(v), safe="")

    def default_type(frm: str, to: str) -> int | None:
        s, d = hs.call("GET", f"/crm/v4/associations/{frm}/{to}/labels")
        if s != 200:
            return None
        rows = d.get("results", [])
        # Prefer the unlabelled type; fall back to the first available.
        plain = [r for r in rows if not r.get("label")]
        return (plain or rows)[0]["typeId"] if (plain or rows) else None

    def index(ot: str, key: str) -> dict[str, str]:
        out, after = {}, None
        while True:
            body = {"filterGroups": [{"filters": [{"propertyName": key,
                                                   "operator": "HAS_PROPERTY"}]}],
                    "properties": [key], "limit": 100}
            if after:
                body["after"] = after
            s, d = hs.call("POST", f"/crm/v3/objects/{ot}/search", body)
            if s != 200:
                return out
            for r in d.get("results", []):
                v = r["properties"].get(key)
                if v:
                    out[str(v)] = r["id"]
            after = (d.get("paging") or {}).get("next", {}).get("after")
            if not after:
                return out

    def link(frm: str, to: str, pairs: list[tuple[str, str]], label: str) -> None:
        if not pairs:
            print(f"    {label}: nothing to link")
            return
        type_id = default_type(frm, to)
        if type_id is None:
            print(f"    {label}: no association type between these objects — skipped")
            return
        made = 0
        for i in range(0, len(pairs), 100):
            inputs = [{"from": {"id": a}, "to": {"id": b},
                       "types": [{"associationCategory": "USER_DEFINED",
                                  "associationTypeId": type_id}]}
                      for a, b in pairs[i:i + 100]]
            s, d = hs.call("POST", f"/crm/v4/associations/{frm}/{to}/batch/create",
                           {"inputs": inputs})
            made += len(d.get("results", []))
            if s not in (200, 201):
                print(f"      ! {label} HTTP {s} {str(d.get('message'))[:120]}")
        print(f"    {label}: {made}/{len(pairs)} linked (type {type_id})")

    print("\n== associations ==")
    companies = index("companies", "ea_customer_number")
    equipment = index(ids["equipment"], "ea_equipment_number") if ids.get("equipment") else {}
    meters = index(ids["ea_meter"], "ea_meter_key") if ids.get("ea_meter") else {}
    calls = index(ids["ea_service_call"], "ea_call_number") if ids.get("ea_service_call") else {}
    contracts = index(ids["contract"], "ea_contract_number") if ids.get("contract") else {}

    custs = list(itertools.islice(cj.customers(page_size=100), 400))
    num_by_id = {c["customerId"]: c["customerNumber"] for c in custs}

    eq_owner: dict[str, str] = {}
    if equipment:
        pairs = []
        for e in itertools.islice(cj.active_equipment(page_size=100), 400):
            number = str(e.get("equipmentNumber") or "")
            owner = num_by_id.get(e.get("customerId"))
            eq_owner[number] = owner or ""
            if number in equipment and owner in companies:
                pairs.append((equipment[number], companies[owner]))
        link(ids["equipment"], "companies", pairs, "Equipment -> Company")

    if meters and equipment:
        # Meter keys are <equipmentNumber>|<meterTypeCode>, so the parent is in the key.
        link(ids["ea_meter"], ids["equipment"],
             [(mid, equipment[k.split("|")[0]]) for k, mid in meters.items()
              if k.split("|")[0] in equipment],
             "Meter -> Equipment")
        link(ids["ea_meter"], "companies",
             [(mid, companies[eq_owner.get(k.split("|")[0], "")])
              for k, mid in meters.items()
              if eq_owner.get(k.split("|")[0]) in companies],
             "Meter -> Company")

    if calls:
        link(ids["ea_service_call"], "companies",
             [(calls[str(c["callNumber"]).strip()], companies[num_by_id[c["customerId"]]])
              for c in itertools.islice(cj.open_service_calls(page_size=100), 200)
              if str(c.get("callNumber") or "").strip() in calls
              and num_by_id.get(c.get("customerId")) in companies],
             "Service Call -> Company")

    if contracts:
        pairs = []
        for c in itertools.islice(cj.active_contracts(page_size=100), 300):
            key = str(c.get("contractNumber") or c.get("contractId"))
            owner = num_by_id.get(c.get("customerId"))
            if key in contracts and owner in companies:
                pairs.append((contracts[key], companies[owner]))
        link(ids["contract"], "companies", pairs, "Contract -> Company")


def roll_up_meters(hs: HubSpot, ids: dict) -> None:
    """Put the three volumes a rep filters on onto Equipment.

    Detail belongs on the Meter object — 69% of machines carry more than one meter, so
    it cannot live in flat columns. But nobody filters a child object, so B/W, Colour
    and Total roll up here.

    The fallback to mfgSuggestedMonthlyVolume is deliberate. The rolling averages read
    0.0 wherever e-automate has no reading history, and rendering that 0 as a volume
    says the machine prints nothing — which is wrong in the expensive direction when
    sizing a fleet. The manufacturer's rated volume is at least a real number.
    """
    if not (ids.get("equipment") and ids.get("ea_meter")):
        return
    sys.path.insert(0, os.getcwd())
    from ceojuice import CeoJuiceClient, CeoJuiceError

    cj = CeoJuiceClient()
    seg = lambda v: urllib.parse.quote(str(v), safe="")
    s, d = hs.call("POST", f"/crm/v3/objects/{ids['equipment']}/search",
                   {"filterGroups": [{"filters": [{"propertyName": "ea_equipment_number",
                                                   "operator": "HAS_PROPERTY"}]}],
                    "properties": ["ea_equipment_number"], "limit": 100})
    numbers = [r["properties"]["ea_equipment_number"] for r in d.get("results", [])]

    rows = []
    for number in numbers:
        try:
            meters = cj.get(
                f"/api/MeterReadings/EquipmentMetersByEqNo/{seg(number)}") or []
        except CeoJuiceError:
            continue
        if not meters:
            continue
        value = lambda m: (m.get("avgMonthlyVolume12Mo")
                           or m.get("mfgSuggestedMonthlyVolume") or 0)
        pick = lambda code: next((value(m) for m in meters
                                  if (m.get("meterType") or {}).get("meterTypeCode") == code), 0)
        rows.append({"idProperty": "ea_equipment_number", "id": number, "properties": {
            "ea_equipment_number": number,
            "ea_meter_count": len(meters),
            "ea_bw_avg_monthly_volume12_mo": pick("B\\W"),
            "ea_color_avg_monthly_volume12_mo": pick("Color"),
            # Total Count is e-automate's own all-clicks meter and equals the sum of the
            # others where present; fall back to summing when the machine has no such meter.
            "ea_total_avg_monthly_volume12_mo": pick("Total Count") or sum(value(m) for m in meters),
        }})
    for i in range(0, len(rows), 100):
        hs.call("POST", f"/crm/v3/objects/{ids['equipment']}/batch/upsert",
                {"inputs": rows[i:i + 100]})
    nonzero = sum(1 for r in rows if r["properties"]["ea_total_avg_monthly_volume12_mo"])
    print(f"    meter rollups: {len(rows)} machines, {nonzero} with a non-zero volume")


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true", help="show what would change")
    g.add_argument("--apply", action="store_true", help="create objects and properties")
    ap.add_argument("--load", action="store_true", help="also load sample e-automate records")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    token = os.environ.get("HUBSPOT_TOKEN")
    if not token:
        print("Set HUBSPOT_TOKEN for the target portal.", file=sys.stderr)
        return 2

    hs = HubSpot(token, dry=args.plan)
    _, who = hs.call("GET", "/account-info/v3/details")
    print(f"portal {who.get('portalId')} ({who.get('accountType')})"
          f"{'  [PLAN ONLY]' if args.plan else ''}")

    ids = provision(hs)

    if args.load and args.apply:
        if not os.environ.get("CEOJUICE_USERNAME"):
            print("\n! --load needs CEOJUICE_USERNAME / CEOJUICE_PASSWORD", file=sys.stderr)
            return 2
        load_sample(hs, ids, args.limit)
        # Records without edges are orphans, so this is part of loading, not a nicety.
        wire_associations(hs, ids)
        roll_up_meters(hs, ids)

    print("\nDone. Not built here, on purpose: lookup resolution (18 code-table "
          "fields should sync as a label, not an id) and phase 2 (381 properties).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
