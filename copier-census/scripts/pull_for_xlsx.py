"""Pull the live state of the dealer census for the Excel workbook.

Everything here comes from HubSpot right now, not from any snapshot on disk — the on-disk
index went stale mid-session and nearly caused duplicate creations, so nothing in the
deliverable is allowed to come from it.
"""
import os, sys, json, re, urllib.request, urllib.error, time
sys.path.insert(0, '/tmp')
from resolver import Companies
from collections import defaultdict, Counter

S = '/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H = {"Authorization": "Bearer " + os.environ['TOKEN'], "Content-Type": "application/json"}

def post(p, b):
    for a in range(6):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + p,
                                       data=json.dumps(b).encode(), headers=H)
            return json.loads(urllib.request.urlopen(r, timeout=90).read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503):
                time.sleep(2 * (a + 1)); continue
            return {'_err': e.code}
        except Exception:
            time.sleep(2 * (a + 1))
    return {}

CO_PROPS = ["name","domain","city","state","phone","copier_company","ai__dealer_verdict",
            "ai__acquisition_status","ai__acquired_by","ai__verification_date",
            "numberofemployees","annualrevenue","ai__enx_elite_dealer","website",
            # the AI research properties, so the coverage sheet carries what we actually know
            # about each dealer and not just a contact count. Only properties with a real
            # fill rate are here - an all-blank column is worse than no column.
            "ai__company_type","ai__brands_carried","ai__dealer_services",
            "ai__locations_served","ai__location_count","ai__enrichment_notable",
            "ai__marketing_maturity","ai__enx_elite_years","ai__revenue_tier_reported",
            "ai__acquisition_year","ai__data_quality_status","ai__data_quality_issues",
            "ai__data_quality_notes","ai__executives","ai__software_stack",
            "ai__has_blog","ai__has_gated_content","ai__hubspot_usage_evidence",
            "ai__open_roles","ai__engagement_overview","ai__trade_press_profile_url",
            "ai__url_leadership","ai__url_contact","ai__url_careers","ai__url_news",
            "ai__accomplishments","ai__growth_commentary","ai__fastest_growing_segment",
            "ai__leasing_partners","ai__manufacturer_awards","ai__acquisitions_made",
            "ai__copier_reason","ai__enrichment_hold","ai__brand_status"]
comps, after = {}, None
while True:
    b = {"filterGroups": [{"filters": [{"propertyName": "copier_company",
                                        "operator": "EQ", "value": "true"}]}],
         "properties": CO_PROPS, "limit": 100}
    if after:
        b["after"] = after
    r = post("/crm/v3/objects/companies/search", b)
    for c in r.get("results", []):
        comps[c["id"]] = c["properties"]
    after = (r.get('paging') or {}).get('next', {}).get('after')
    if not after:
        break
    time.sleep(0.12)
print(f"dealer companies: {len(comps)}")

CT_PROPS = ["firstname","lastname","jobtitle","email","phone","mobilephone","hs_lead_status",
            "linkedin_profile_url__unique_value","associatedcompanyid","company",
            "neverbouncevalidationresult","validated__linkedin_or_manually",
            "ai__contact_verified_date","ai__li_still_at_company","zoominfo_contact_accuracy_score_",
            "hs_seniority","createdate","ai__contact_evidence"]
ids = list(comps)
per, seen = defaultdict(list), set()
for i in range(0, len(ids), 40):
    chunk, after = ids[i:i+40], None
    while True:
        b = {"filterGroups": [{"filters": [{"propertyName": "associatedcompanyid",
                                            "operator": "IN", "values": chunk}]}],
             "properties": CT_PROPS, "limit": 100}
        if after:
            b["after"] = after
        r = post("/crm/v3/objects/contacts/search", b)
        for c in r.get("results", []):
            if c['id'] in seen:
                continue
            seen.add(c['id'])
            p = c['properties']; p['id'] = c['id']
            per[str(p.get('associatedcompanyid') or '')].append(p)
        after = (r.get('paging') or {}).get('next', {}).get('after')
        if not after:
            break
        time.sleep(0.1)
    time.sleep(0.08)
print(f"contacts at dealer companies: {len(seen)}")

hold = set(json.load(open(S + '/freeze_final.json'))['hard'])
brand = {}
import glob
for f in glob.glob(S + '/brand/out/b_*.jsonl'):
    for l in open(f):
        l = l.strip()
        if not l:
            continue
        try:
            o = json.loads(l)
        except Exception:
            continue
        idl = o.get('ids') or []
        if isinstance(idl, str):
            idl = [x for x in idl.split(';') if x]
        for x in idl:
            brand[x] = o
# what the sweep tried, per dealer, so the gap sheet can say what to try NEXT
tried = {}
for f in glob.glob(S + '/cov/out/c_*.jsonl') + glob.glob(S + '/cov2/out/d_*.jsonl') \
       + glob.glob(S + '/deep/out/e_*.jsonl'):
    for l in open(f):
        l = l.strip()
        if not l:
            continue
        try:
            o = json.loads(l)
        except Exception:
            continue
        if o.get('dealer_summary') or o.get('found_count') is not None:
            cl = str(o.get('cluster') or '')
            if cl:
                prev = tried.get(cl, {})
                tried[cl] = {
                    'sources_tried': o.get('sources_tried') or prev.get('sources_tried'),
                    'why_not_found': o.get('why_not_found') or prev.get('why_not_found'),
                    'status': o.get('status') or prev.get('status'),
                    'note': (o.get('company_note') or prev.get('note') or '')[:600]}

json.dump({'companies': comps, 'contacts': {k: v for k, v in per.items()},
           'hold': sorted(hold), 'brand': brand, 'tried': tried},
          open(S + '/xlsx_data.json', 'w'))
print("saved xlsx_data.json")
