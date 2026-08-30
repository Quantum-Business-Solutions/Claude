"""Map every old private-label destination to its Praxera replacement.

Emails cannot link to an unpublished page: the live URL 404s until publish, and
the draft is only reachable behind an hs_preview key that is not public-safe and
not stable. So the workable order is to write the FINAL praxerasupplements.com
URL into the email now and hold the email in draft until the page publishes --
the link starts working the moment the page goes live, with nothing to rewrite.

Matches are proposed by slug and title similarity and are labelled by how much
they can be trusted. EXACT means the old slug survives into the new build.
LIKELY means one new page clearly covers the same subject. NONE means nothing on
the new site covers it -- those are the rows that need a decision, and they are
the point of the exercise.
"""
import json,re,collections,difflib

M=json.load(open("reference/merged_audit.json"))
idx=json.load(open("reference/page_index.json"))
NEW="https://www.praxerasupplements.com/"
new=[p["slug"] for p in idx["production"]]

def norm(s):
    s=s.lower()
    s=re.sub(r"^https?://[^/]+/","",s)
    s=re.sub(r"[?#].*$","",s)
    s=s.strip("/")
    s=re.sub(r"^(en/)?(pl-demo-)?","",s)
    s=re.sub(r"^private-label(ing)?[-/]?","",s)
    s=re.sub(r"[^a-z0-9]+"," ",s).strip()
    return s

newmap={norm(s):s for s in new}
newkeys=list(newmap)

# hand-set the ones a string match cannot reach; these are editorial calls
MANUAL={
 "private-label-get-started":"en/pl-demo-get-started",
 "private-labeling":"pl-demo-about",
 "private-label-supplements-resource-center":"en/pl-demo-resources",
 "private-label-supplements-guide":"pl-demo-guides",
 "thank-you-guide-private-labeling-supplements":"en/pl-demo-ty-guide",
 "ingredients-testing-certification-guide":"pl-demo-ingredients-testing",
 "thank-you-ingredients-testing-certification-guide":"en/pl-demo-ty-guide",
 "private-label-supplements-client-onboarding":"en/pl-demo-onboarding-guide",
 "thank-you-client-onboarding":"en/pl-demo-ty-onboarding",
 "thank-you-private-labeling":"en/pl-demo-ty-consultation",
 "ty-private-label-supplements":"en/pl-demo-ty-consultation",
 "thank-you-start-private-labeling":"en/pl-demo-ty-consultation",
 "private-labeling-dropship":"en/pl-demo-dropshipping",
 "private-labeling-how-to-sell-supplements":"en/pl-demo-how-to-sell-supplements",
 "private-labeling-supplement-manufacturer":"pl-demo-about",
 "dv-pl-our-design-services":"en/pl-demo-design-team",
 "dv-pl-design-main-page":"pl-demo-design-services",
 "dv-pl-customer-supplied-art":"en/pl-demo-customer-art",
}

def match(url):
    slug=re.sub(r"^https?://[^/]+/","",url).split("?")[0].strip("/")
    if slug in MANUAL: return MANUAL[slug],"MANUAL"
    n=norm(url)
    if n in newmap: return newmap[n],"EXACT"
    c=difflib.get_close_matches(n,newkeys,n=1,cutoff=0.78)
    if c: return newmap[c[0]],"LIKELY"
    return None,"NONE"

# every destination an email actually points at, weighted by how many link there
dest=collections.Counter()
for e in M["emails_linking_to_pl"]:
    for u in e["pl_urls"]: dest[u.split("?")[0]]+=1

rows=[]
for u,n in dest.most_common():
    tgt,how=match(u)
    rows.append({"old":u,"emails":n,"new":(NEW+tgt) if tgt else None,"confidence":how})

# and every asset in Patrick's inventory, email-linked or not
for a in M["patrick_assets_rechecked"]:
    u=a["Live URL"].split("?")[0]
    if any(r["old"]==u for r in rows): continue
    tgt,how=match(u)
    rows.append({"old":u,"emails":0,"new":(NEW+tgt) if tgt else None,
                 "confidence":how,"type":a["Asset Type"],"title":a["Title"]})

json.dump(rows,open("reference/url_map.json","w"),indent=1)
c=collections.Counter(r["confidence"] for r in rows)
print("URL MAP",dict(c),"\n")
print(f"{'emails':>6}  {'confidence':10} {'old':66} -> new")
for r in rows:
    if r["emails"]:
        print(f"{r['emails']:>6}  {r['confidence']:10} {r['old'][:66]:66} -> {(r['new'] or '*** NO TARGET ***')[:60]}")
print("\nNO TARGET ON THE NEW SITE (needs a decision):")
for r in rows:
    if r["confidence"]=="NONE":
        print(f"  {r['emails']:>3} emails  {r['old'][:92]}")
