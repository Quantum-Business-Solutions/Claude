"""Active (DYNAMIC) company lists bucketing Potential Prospect - Lease End Date.

All boundaries are ROLLING, anchored to TODAY, so the lists stay correct as time
passes. A fixed date would freeze the buckets on the day they were built - the
usual way an "active" list quietly goes stale.

HubSpot's indexed timepoints are DIRECTIONAL, which shapes the whole design:
  IS_AFTER  accepts only offsets >= 0   (it can look forward from today)
  IS_BEFORE accepts only offsets <= 0   (it can look backward from today)
  IS_BETWEEN accepts only a NOW <-> TODAY endpoint pair
So a forward-looking band cannot be one BETWEEN. Each band is
  IS_AFTER today+lo          -> the floor
  AND IS_BETWEEN now..today+hi -> the ceiling
"""
import json, os, sys, time, urllib.request, urllib.error

GO = "--go" in sys.argv
H = {"Authorization": "Bearer " + os.environ["PAT"], "Content-Type": "application/json"}
PROP = "potential_prospect__lease_end_date"
ZONE = "America/Chicago"

def req(url, body=None, method="POST"):
    for i in range(6):
        try:
            r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                       headers=H, method=method)
            raw = urllib.request.urlopen(r).read()
            return (json.loads(raw) if raw else {}), None
        except urllib.error.HTTPError as e:
            b = e.read().decode()[:300]
            if e.code in (429, 502, 503, 504): time.sleep(2 * (i + 1)); continue
            return None, "%s %s" % (e.code, b)
        except Exception:
            time.sleep(2 * (i + 1))
    return None, "retries exhausted"

TODAY = lambda d: {"timeType": "INDEXED", "timezoneSource": "CUSTOM", "zoneId": ZONE,
                   "indexReference": {"referenceType": "TODAY"}, "offset": {"days": d}}
NOW    = {"timeType": "INDEXED", "timezoneSource": "CUSTOM", "zoneId": ZONE,
          "indexReference": {"referenceType": "NOW"}}

def floor_after(days):
    """date > today+days  (IS_AFTER is EXCLUSIVE-only)"""
    return {"filterType": "PROPERTY", "property": PROP,
            "operation": {"operator": "IS_AFTER", "includeObjectsWithNoValueSet": False,
                          "operationType": "TIME_POINT", "type": "TIME_POINT",
                          "propertyParser": "VALUE", "endpointBehavior": "EXCLUSIVE",
                          "timePoint": TODAY(days)}}

def ceiling_between(days):
    """now <= date <= today+days"""
    return {"filterType": "PROPERTY", "property": PROP,
            "operation": {"operator": "IS_BETWEEN", "includeObjectsWithNoValueSet": False,
                          "operationType": "TIME_RANGED", "type": "TIME_RANGED",
                          "propertyParser": "VALUE",
                          "lowerBoundEndpointBehavior": "INCLUSIVE",
                          "upperBoundEndpointBehavior": "INCLUSIVE",
                          "lowerBoundTimePoint": NOW, "upperBoundTimePoint": TODAY(days)}}

def before_today():
    """date < today"""
    return {"filterType": "PROPERTY", "property": PROP,
            "operation": {"operator": "IS_BEFORE", "includeObjectsWithNoValueSet": False,
                          "operationType": "TIME_POINT", "type": "TIME_POINT",
                          "propertyParser": "VALUE", "endpointBehavior": "EXCLUSIVE",
                          "timePoint": TODAY(0)}}

# a prospecting list must never surface UBEO's own customers
NOT_CUSTOMER = {"filterType": "PROPERTY", "property": "lifecyclestage",
                "operation": {"operator": "IS_NONE_OF", "includeObjectsWithNoValueSet": True,
                              "operationType": "ENUMERATION", "values": ["customer"]}}

#          label                   floor(days, exclusive)   ceiling(days, inclusive)
BANDS = [("Less than 1 Month",              None,  30),
         ("1-3 Months",                       30,  91),
         ("3-6 Months",                       91, 182),
         ("6-9 Months",                      182, 273),
         ("9-12 Months",                     273, 365),
         ("More than 12 Months",             365, None)]

def build(label, lo, hi):
    fs = []
    if lo is not None: fs.append(floor_after(lo))
    if hi is not None: fs.append(ceiling_between(hi))
    if lo is None and hi is None: fs.append(before_today())
    fs.append(NOT_CUSTOMER)
    return {"name": "Companies - Potential Lease End Date - %s" % label,
            "objectTypeId": "0-2", "processingType": "DYNAMIC",
            "filterBranch": {"filterBranchType": "OR", "filterBranchOperator": "OR", "filters": [],
                "filterBranches": [{"filterBranchType": "AND", "filterBranchOperator": "AND",
                                    "filterBranches": [], "filters": fs}]}}

if not GO:
    for lab, lo, hi in BANDS:
        print("  %-24s  (%s .. %s]" % (lab, "now" if lo is None else "+%dd" % lo,
                                       "inf" if hi is None else "+%dd" % hi))
    sys.exit(0)

made = []
for lab, lo, hi in BANDS:
    d, e = req("https://api.hubapi.com/crm/v3/lists", build(lab, lo, hi))
    if e: print("  FAILED  %-24s %s" % (lab, e)); continue
    made.append((d["list"]["listId"], lab))
    print("  created %-8s %s" % (d["list"]["listId"], d["list"]["name"]))
json.dump(made, open("lease_lists_made.json", "w"))
print("\nresolving memberships...")
time.sleep(50)
tot = 0
for lid, lab in made:
    d, e = req("https://api.hubapi.com/crm/v3/lists/%s/memberships?limit=1" % lid, method="GET")
    n = (d or {}).get("total", "?")
    if isinstance(n, int): tot += n
    print("  %-8s %-24s %s" % (lid, lab, format(n, ",") if isinstance(n, int) else n))
print("  %-33s %s across the new bands" % ("", format(tot, ",")))
