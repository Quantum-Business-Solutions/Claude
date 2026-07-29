#!/usr/bin/env python3
"""Build the CEO Juice -> HubSpot mapping schema view from live portal metadata.

    export HUBSPOT_TOKEN=pat-na1-...
    python scripts/mapping_schema.py docs/live-mapping.json > docs/mapping-schema.html

The mapping rows come from Supabase (dumped to the json file); everything about the
TARGET side is read from the portal at run time -- label, type, whether the value is
read-only, whether it is a unique key, and how many records actually carry a value.

READ-ONLY IS THE POINT OF THE VERIFY STEP. A mapping onto a HubSpot calculated
property is not merely wrong data, it is a 400 on every batch that includes it, which
takes the whole batch down with it. Name similarity cannot see that; only the portal
can tell you.
"""

from __future__ import annotations

import collections
import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.hubapi.com"
TOKEN = os.environ.get("HUBSPOT_TOKEN") or sys.exit("HUBSPOT_TOKEN not set")


def call(method: str, path: str, body=None, tries: int = 4):
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {TOKEN}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": e.code, "__body": e.read()[:300].decode("utf-8", "replace")}
        except Exception as e:  # noqa: BLE001 - network flake
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"__error": "net", "__body": str(e)}
    return {"__error": "exhausted"}


# ── Object identity ─────────────────────────────────────────────────────────
# Custom-object ids differ per portal, so resolve labels rather than hardcoding.
STANDARD = {
    "company": "Company", "contact": "Contact", "deal": "Deal",
    "line_items": "Line item", "products": "Product", "tickets": "Ticket",
}


def object_labels() -> dict[str, str]:
    labels = dict(STANDARD)
    schemas = call("GET", "/crm/v3/schemas").get("results", [])
    for s in schemas:
        labels[s["objectTypeId"]] = s.get("labels", {}).get("singular") or s["name"]
        labels[s["fullyQualifiedName"]] = labels[s["objectTypeId"]]
    return labels


def properties(obj: str) -> dict[str, dict]:
    r = call("GET", f"/crm/v3/properties/{urllib.parse.quote(obj)}")
    out = {}
    for p in r.get("results", []):
        mm = p.get("modificationMetadata") or {}
        out[p["name"]] = {
            "label": p.get("label") or p["name"],
            "type": p.get("type"),
            "field": p.get("fieldType"),
            "group": p.get("groupName"),
            "unique": bool(p.get("hasUniqueValue")),
            "calculated": bool(p.get("calculated")),
            "read_only": bool(mm.get("readOnlyValue")),
            "options": len(p.get("options") or []),
        }
    return out


def record_count(obj: str) -> int | None:
    r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/search",
             {"limit": 1, "properties": ["hs_object_id"]})
    return r.get("total") if "__error" not in r else None


def fill(obj: str, prop: str, total: int) -> int | None:
    """How many records carry a value. Cheap: a HAS_PROPERTY search returns a total."""
    if not total:
        return 0
    r = call("POST", f"/crm/v3/objects/{urllib.parse.quote(obj)}/search",
             {"limit": 1, "properties": ["hs_object_id"],
              "filterGroups": [{"filters": [{"propertyName": prop,
                                             "operator": "HAS_PROPERTY"}]}]})
    return r.get("total") if "__error" not in r else None


# ── Verdicts ────────────────────────────────────────────────────────────────
def verdict(row: dict, meta: dict | None) -> tuple[str, str]:
    """(severity, why). Severity drives the badge; why is shown verbatim."""
    if meta is None:
        return ("missing", "Target property does not exist in this portal. "
                           "The sync will 400 on every write.")
    if row["e"] and meta["read_only"]:
        kind = "calculated by HubSpot" if meta["calculated"] else "read-only"
        return ("blocked", f"Target is {kind}. HubSpot rejects the write, and the "
                           f"whole batch fails with it -- not just this field.")
    if not row["e"]:
        return ("quarantined", row.get("n") or "Disabled.")
    if row["k"] and not meta["unique"]:
        return ("weakkey", "Used as the match key but the property is not unique in "
                           "HubSpot, so two source rows can collide onto one record.")
    if row["k"]:
        return ("key", "Match key, unique in HubSpot.")
    if row["d"] == "both" and meta["read_only"]:
        return ("blocked", "Two-way onto a read-only property.")
    return ("ok", "")


SEV = {
    "blocked":     ("Blocked", "#b91c1c"),
    "missing":     ("Missing target", "#b91c1c"),
    "weakkey":     ("Unsafe key", "#c2410c"),
    "quarantined": ("Quarantined", "#78716c"),
    "key":         ("Match key", "#047857"),
    "ok":          ("", ""),
}

# Priority order for the custom objects, so a portal capped at ten knows which ten.
# Ranked by what a fleet assessment and a renewal cannot be done without.
PRIORITY = [
    ("Equipment", "The fleet. Nothing else in the integration means anything without "
                  "the machine list -- a renewal, an assessment and a service history "
                  "all hang off it."),
    ("Contract", "What each machine is billed under. Drives expiry, base rate and "
                 "overage, which is the whole renewal conversation."),
    ("Meter", "Volume. 69% of machines carry more than one meter, so this cannot be "
              "columns on Equipment without one meter overwriting another."),
    ("Lease", "Assembled from ContractDetail plus Contract because e-automate exposes "
              "no lease route. Only object that can answer 'what is the buyout'."),
    ("Service Call", "Service history. Needed to argue reliability, and its own object "
                     "rather than Tickets so a dealer's call volume does not swamp the "
                     "agency's own pipelines."),
    ("Invoice", "Actual spend. Wanted for a true cost-per-page but currently one "
                "property deep -- the least built-out of the six."),
]


def main() -> None:
    rows = json.load(open(sys.argv[1]))
    labels = object_labels()

    objs = sorted({r["ho"] for r in rows})
    meta = {o: properties(o) for o in objs}
    counts = {o: record_count(o) for o in objs}

    # Fill rate only for enabled rows whose target exists -- one search each.
    fills: dict[tuple[str, str], int | None] = {}
    for r in rows:
        key = (r["ho"], r["hp"])
        if r["e"] and key not in fills and r["hp"] in meta[r["ho"]]:
            fills[key] = fill(r["ho"], r["hp"], counts.get(r["ho"]) or 0)

    by_obj = collections.defaultdict(list)
    for r in rows:
        m = meta[r["ho"]].get(r["hp"])
        sev, why = verdict(r, m)
        r["_m"], r["_sev"], r["_why"] = m, sev, why
        r["_fill"] = fills.get((r["ho"], r["hp"]))
        by_obj[r["ho"]].append(r)

    tally = collections.Counter(r["_sev"] for r in rows)
    print(json.dumps({
        "objects": {labels.get(o, o): {
            "id": o,
            "records": counts.get(o),
            "mappings": len(by_obj[o]),
            "enabled": sum(1 for r in by_obj[o] if r["e"]),
            "rows": [{k: v for k, v in r.items() if k != "_m"} | {"meta": r["_m"]}
                     for r in sorted(by_obj[o], key=lambda x: (not x["k"], x["co"], x["cp"]))],
        } for o in objs},
        "tally": dict(tally),
        "priority": PRIORITY,
    }, indent=1))


if __name__ == "__main__":
    main()
