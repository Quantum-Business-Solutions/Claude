"""Merge Patrick's June audit with the live scan, and make every row defend itself.

Two audits of the same portal, taken two months apart by different methods, is
a gift: where they agree the number is trustworthy, and where they disagree the
disagreement is itself the finding. Patrick scanned URLs and links; this repo
scanned forms, flows and email bodies. Neither alone is the answer.

Every asset carries an EVIDENCE string naming the specific thing that made it
private label -- a slug, an href, a form GUID on a page -- because "it has
Private Label in the name" is how PetTechLabs ends up on a DaVinci migration
list. Rows that only ever matched a name are marked WEAK on purpose.
"""
import json,os,re,time,urllib.request,urllib.error,collections
import concurrent.futures as cf

T=os.environ["TOKEN"]
def get(u,tr=5):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(
            urllib.request.Request(u,headers={"Authorization":"Bearer "+T}),timeout=60))
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            if e.code not in (429,502,503,504) or i==tr-1: raise
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

# Sibling brands share this portal. Anything matching these is not DaVinci PL.
SIBLING=re.compile(r"(pettechlabs|pet tech|\bPTL\b|vetriscience|vetri-science|little davinci|d4hcp)",re.I)

P=json.load(open("reference/patrick/migration_audit_june25.json"))
EV=json.load(open("reference/email_evidence.json"))
SCAN=json.load(open("reference/pl_dependency_scan.json"))
MINE=json.load(open("reference/migration_assets.json"))
DEPS=json.load(open("reference/live_workflow_deps.json"))

verified={r["id"] for r in EV if r.get("verdict")=="LINK"}
ev_by_id={r["id"]:r for r in EV}

out={"generated":time.strftime("%Y-%m-%d %H:%M UTC",time.gmtime()),
     "sources":{"patrick_audit":"DaVinci_PrivateLabel_Migration_Audit_1.xlsx (June 25 2026)",
                "live_scan":"reference/pl_dependency_scan.json + email_evidence.json"}}

# ---------------------------------------------------------------- emails
emails=[]
for r in EV:
    if r.get("verdict")!="LINK": continue
    name=r.get("name","")
    emails.append({"id":r["id"],"name":name,"state":r.get("state",""),
        "pl_urls":r["pl_urls"],
        "evidence":f'links to {r["pl_urls"][0]}',
        "strength":"STRONG",
        "cross_brand":bool(SIBLING.search(name))})
out["emails_linking_to_pl"]=sorted(emails,key=lambda x:x["name"])

# emails Patrick found that the live scan did NOT verify -> did they change or vanish?
p_email_ids={r["Email ID"] for r in P["email_links"] if r.get("Email ID")}
out["reconciliation_emails"]={
    "patrick_distinct_emails":len(p_email_ids),
    "live_verified":len(verified),
    "in_patrick_not_live":sorted(p_email_ids-verified)[:40],
    "in_live_not_patrick":sorted(verified-p_email_ids)[:40],
    "agree_both":len(p_email_ids&verified)}

# ------------------------------------------------------------- workflows
wf=[]
for f in SCAN["flows"]:
    kept=[e for e in f["pl_emails"] if e[0] in verified]
    name=f["name"]
    named=bool(re.search(r"private[ _-]?label|praxera",name,re.I))
    if not (f["literal_pl_link"] or kept or named): continue
    ev=[]
    if f["literal_pl_link"]: ev.append("a PL URL appears in a workflow action")
    if kept: ev.append(f'sends {len(kept)} verified PL email(s), e.g. "{kept[0][1][:50]}"')
    if named and not ev: ev.append("name only -- no PL link and no verified PL email")
    wf.append({"id":f["id"],"name":name,"live":f["live"],"updated":f["updated"],
        "verified_emails":kept,
        "evidence":"; ".join(ev),
        "strength":"STRONG" if (f["literal_pl_link"] or kept) else "WEAK",
        "cross_brand":bool(SIBLING.search(name))})
out["workflows"]=sorted(wf,key=lambda x:(not x["live"],x["name"]))

# ------------------------------------------------------ forms on new site
out["forms_on_new_site"]=[{**f,
    "evidence":f'embedded on {len(f["pages"])} new page(s): {", ".join(f["pages"][:3])}',
    "strength":"STRONG",
    "gap":"no live workflow listens to this form"} for f in MINE["forms_on_new_site"]]

# ----------------------------------------------------- Patrick's assets, live
def recheck(r):
    hid=r.get("HubSpot ID","").strip()
    t=r["Asset Type"]
    if not hid or t=="Main-site page":
        return {**r,"live_status":"n/a (not in HubSpot)"}
    ep={"Blog post":"/cms/v3/blogs/posts/","Landing page":"/cms/v3/pages/landing-pages/",
        "Site page":"/cms/v3/pages/site-pages/"}[t]
    d=get(ep+hid)
    if d is None: return {**r,"live_status":"GONE (404)"}
    return {**r,"live_status":d.get("state",d.get("currentState","?")),
            "live_slug":d.get("slug",""),"live_updated":str(d.get("updated",""))[:10]}
with cf.ThreadPoolExecutor(6) as ex:
    assets=list(ex.map(recheck,P["asset_inventory"]))
for a in assets:
    url=a.get("Live URL","")+" "+a.get("Slug","")
    if "/private-label/" in url or "private-label" in a.get("Slug",""):
        a["evidence"]=f'slug/URL contains private-label: {a.get("Slug") or a.get("Live URL")}'
        a["strength"]="STRONG"
    elif re.search(r"private[ -]?label",a.get("Title",""),re.I):
        a["evidence"]=f'title only: "{a["Title"][:60]}"'
        a["strength"]="MEDIUM"
    else:
        a["evidence"]="carried from Patrick's audit; no PL token in slug or title"
        a["strength"]="WEAK"
    a["cross_brand"]=bool(SIBLING.search(a.get("Title","")+url))
    a["slug_drifted"]= bool(a.get("live_slug") and a.get("Slug") and a["live_slug"]!=a["Slug"])
out["patrick_assets_rechecked"]=assets

json.dump(out,open("reference/merged_audit.json","w"),indent=1)

# ------------------------------------------------------------------ report
def h(t): print("\n"+"="*78+"\n"+t+"\n"+"="*78)
h("MERGED PRIVATE-LABEL ASSET AUDIT")
print(f"Patrick's audit (Jun 25) + live scan ({out['generated']})")
r=out["reconciliation_emails"]
h("1. EMAILS LINKING TO A PRIVATE-LABEL PAGE")
print(f"  Patrick found : {r['patrick_distinct_emails']} distinct emails")
print(f"  Live verified : {r['live_verified']}")
print(f"  Agree on      : {r['agree_both']}")
print(f"  Only Patrick  : {len(set(p_email_ids)-verified)}   (deleted, unpublished, or link removed since June)")
print(f"  Only live     : {len(verified-set(p_email_ids))}   (new since June, or Praxera-era)")
print(f"  Rejected as token-only false positives: {sum(1 for e in EV if e.get('verdict')=='TOKEN')}")
h("2. WORKFLOWS")
s=collections.Counter((w['strength'],w['live']) for w in out["workflows"])
print(f"  total {len(out['workflows'])}   live {sum(1 for w in out['workflows'] if w['live'])}")
print(f"  STRONG evidence: {sum(1 for w in out['workflows'] if w['strength']=='STRONG')}"
      f"   WEAK (name only): {sum(1 for w in out['workflows'] if w['strength']=='WEAK')}")
xb=[w for w in out["workflows"] if w["cross_brand"]]
print(f"  cross-brand rows flagged for removal: {len(xb)}  {[w['name'][:32] for w in xb]}")
h("3. PATRICK'S 105 ASSETS, RE-CHECKED LIVE")
print("  ",dict(collections.Counter(a["live_status"] for a in assets)))
print("   strength:",dict(collections.Counter(a["strength"] for a in assets)))
drift=[a for a in assets if a["slug_drifted"]]
print(f"   slug drifted since June: {len(drift)}")
for a in drift[:8]: print(f"     {a['Title'][:44]:46} {a['Slug'][:34]} -> {a['live_slug'][:34]}")
print("\nwrote reference/merged_audit.json")
