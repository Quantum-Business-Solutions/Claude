"""Create 'AI - Potential Lease End Date' on Company and backfill it from the
date already stated at the front of ai__lease_information.

  PAT=<ubeo token> python3 lease_date_deploy.py            # dry run
  PAT=<ubeo token> python3 lease_date_deploy.py --go       # create + write

Reads nothing but ai__lease_information. Never modifies that field.
"""
import json, os, sys, time, urllib.request, urllib.error, collections, socket
from lease_date_parse import parse, to_hubspot
socket.setdefaulttimeout(60)

GO = "--go" in sys.argv
H = {"Authorization": "Bearer " + os.environ["PAT"], "Content-Type": "application/json"}
PROP = "ai__potential_lease_end_date"
CONF = "ai__lease_date_confidence"

def req(url, body=None, method="POST"):
    for i in range(6):
        try:
            r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                       headers=H, method=method)
            return json.load(urllib.request.urlopen(r)), None
        except urllib.error.HTTPError as e:
            b = e.read().decode()[:200]
            if e.code in (429, 502, 503, 504): time.sleep(2 * (i + 1)); continue
            return None, "%s %s" % (e.code, b)
        except Exception:
            time.sleep(2 * (i + 1))
    return None, "retries exhausted"

DEFS = [
 {"name": PROP, "label": "AI - Potential Lease End Date", "type": "date", "fieldType": "date",
  "groupName": "companyinformation",
  "description": "The lease end date stated at the front of AI - Lease Information, as a real date so it can be "
                 "sorted, filtered and used in lists and workflows. Set to the LAST day of the stated month. "
                 "Read AI - Lease Information for the evidence and the confidence behind it - some of these "
                 "dates are projections, not confirmed dates."},
 {"name": CONF, "label": "AI - Lease Date Confidence", "type": "enumeration", "fieldType": "select",
  "groupName": "companyinformation",
  "description": "How the Potential Lease End Date was arrived at. CONFIRMED and CALCULATED come from something "
                 "the prospect actually said. PROJECTED assumes a renewal that has not been confirmed. "
                 "MONTH ASSUMED means only a year was ever stated.",
  "options": [{"label": l, "value": v, "displayOrder": i} for i, (l, v) in enumerate([
      ("Confirmed - stated date", "confirmed"),
      ("Calculated - from a stated term", "calculated"),
      ("Month assumed - only a year was stated", "month_assumed"),
      ("Projected - assumes an unconfirmed renewal", "projected"),
      ("Month-to-month - no lease term", "month_to_month"),
      ("Unspecified", "unspecified")])]},
]

def bucket(tier, month_real):
    t = (tier or "").upper()
    if "MONTH-TO-MONTH" in t or "MONTH TO MONTH" in t: return "month_to_month"
    if "PROJECTED" in t: return "projected"
    if not month_real: return "month_assumed"
    if "CONFIRMED" in t: return "confirmed"
    if "CALCULATED" in t or "COMPUTED" in t: return "calculated"
    return "unspecified"

# ---- 1. properties
for d in DEFS:
    got, _ = req("https://api.hubapi.com/crm/v3/properties/companies/%s" % d["name"], method="GET")
    if got: print("property exists : %s" % d["name"]); continue
    if not GO: print("property WOULD BE CREATED : %s" % d["name"]); continue
    _, e = req("https://api.hubapi.com/crm/v3/properties/companies", d)
    print("property created: %s%s" % (d["name"], "  ERROR %s" % e if e else ""))

# ---- 2. every company that carries a lease signal
after, comps = None, {}
while True:
    body = {"limit": 200, "properties": ["name", "ai__lease_information", PROP],
            "filterGroups": [{"filters": [{"propertyName": "ai__lease_information",
                                           "operator": "HAS_PROPERTY"}]}]}
    if after: body["after"] = after
    d, e = req("https://api.hubapi.com/crm/v3/objects/companies/search", body)
    if e: print("search failed: %s" % e); break
    for r in d.get("results", []): comps[r["id"]] = r["properties"]
    after = d.get("paging", {}).get("next", {}).get("after")
    if not after: break
    time.sleep(0.2)
print("\ncompanies carrying ai__lease_information : %s" % format(len(comps), ","))

writes, skip_nodate, already, tiers = [], 0, 0, collections.Counter()
for cid, p in comps.items():
    r = parse(p.get("ai__lease_information"))
    if r is None: skip_nodate += 1; continue
    d, tier, month_real = r
    b = bucket(tier, month_real); tiers[b] += 1
    if p.get(PROP): already += 1; continue
    writes.append({"id": cid, "properties": {PROP: to_hubspot(d), CONF: b}})
print("  parse to a date        : %s" % format(len(comps) - skip_nodate, ","))
print("  no usable date prefix  : %s" % format(skip_nodate, ","))
print("  date already populated : %s" % format(already, ","))
print("  TO WRITE               : %s" % format(len(writes), ","))
print("\nconfidence split:")
for k, n in tiers.most_common(): print("   %-16s %s" % (k, format(n, ",")))

if not GO:
    print("\ndry run - re-run with --go to create the properties and write")
    json.dump(writes, open("lease_date_writes.json", "w"))
    sys.exit(0)

done = 0
for i in range(0, len(writes), 100):
    d, e = req("https://api.hubapi.com/crm/v3/objects/companies/batch/update",
               {"inputs": writes[i:i + 100]})
    if e: print("  batch %d failed: %s" % (i // 100, e)); continue
    done += len(d.get("results", []))
    time.sleep(0.15)
print("\nWROTE %s companies" % format(done, ","))
