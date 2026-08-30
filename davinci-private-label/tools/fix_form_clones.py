"""Take the remaining DaVinci out of the Praxera form clones -- where it can come out.

Three different things look the same on the rendered form and are not the same:

  privacyText          per-form, editable, stored on the form record. Fixable.
  postSubmitAction     the redirect after submit, still pointing at a DaVinci
                       thank-you page. Fixable, and safe to point at the final
                       Praxera URL now because no clone is live yet.
  property NAME        i_would_like_to_subscribe_to_the_davinci_blog is a CONTACT
                       PROPERTY internal name, shared with every other form and
                       every contact record in the portal. It is not form copy and
                       renaming it is a portal-wide change, so it is left alone and
                       reported. The LABEL a visitor reads is separate and is fixed.
"""
import json,os,re,sys,urllib.request,urllib.error

T=os.environ["TOKEN"]
NEW="https://www.praxerasupplements.com/"
REDIRECT={
 "thank-you-client-onboarding":NEW+"en/pl-demo-ty-onboarding",
 "thank-you-start-private-labeling":NEW+"en/pl-demo-ty-consultation",
 "thank-you-ingredients-testing-certification-guide":NEW+"en/pl-demo-ty-guide",
 "thank-you-guide-private-labeling-supplements":NEW+"en/pl-demo-ty-guide",
 "ty-private-label-supplements":NEW+"en/pl-demo-ty-consultation",
 "thank-you-private-labeling":NEW+"en/pl-demo-ty-consultation",
}
DV=re.compile(r"DaVinci Laboratories|DaVinci Labs|DaVinci",re.I)

def call(m,u,body=None):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    d=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(u,data=d,method=m,
        headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
    try: return json.load(urllib.request.urlopen(r,timeout=60))
    except urllib.error.HTTPError as e:
        print("   HTTP",e.code,e.read().decode()[:400]); return None

def fix_labels(node,log):
    """Rewrite what a visitor reads. Never touch a field's internal name."""
    if isinstance(node,dict):
        out={}
        for k,v in node.items():
            if k=="name":
                out[k]=v
                if isinstance(v,str) and DV.search(v): log.append(("property name (left alone)",v))
            elif k in ("label","placeholder","description","helpText") and isinstance(v,str) and DV.search(v):
                out[k]=DV.sub("Praxera",v); log.append((k,v))
            else:
                out[k]=fix_labels(v,log)
        return out
    if isinstance(node,list): return [fix_labels(x,log) for x in node]
    return node

def main():
    go="--go" in sys.argv
    clones=json.load(open("reference/praxera_form_clones.json"))
    left=[]
    for c in clones:
        f=call("GET",f"/marketing/v3/forms/{c['clone_id']}")
        if not f: continue
        log=[]; changed=False
        body={k:v for k,v in f.items() if k not in ("id","archived","updatedById","createdById")}

        lc=body.get("legalConsentOptions") or {}
        for key in ("privacyText","communicationConsentText","consentToProcessText",
                    "processingConsentText","processingConsentCheckboxLabel"):
            if isinstance(lc.get(key),str) and DV.search(lc[key]):
                lc[key]=DV.sub("Praxera",lc[key]); log.append((f"legalConsent.{key}","rewritten")); changed=True
        if isinstance(lc.get("communicationsCheckboxes"),list):
            for box in lc["communicationsCheckboxes"]:
                for kk in ("label","subscriptionTypeId"):
                    if isinstance(box.get(kk),str) and DV.search(box[kk]) and kk=="label":
                        box[kk]=DV.sub("Praxera",box[kk]); log.append(("consent checkbox label","rewritten")); changed=True
        body["legalConsentOptions"]=lc

        psa=(body.get("configuration") or {}).get("postSubmitAction") or {}
        val=psa.get("value")
        if isinstance(val,str) and "davincilabs.com" in val:
            slug=val.rstrip("/").split("/")[-1].split("?")[0]
            if slug in REDIRECT:
                psa["value"]=REDIRECT[slug]; changed=True
                log.append(("redirect",f"{slug} -> {REDIRECT[slug]}"))
            else:
                left.append((c["clone_name"],"redirect",val))

        body["fieldGroups"]=fix_labels(body.get("fieldGroups",[]),log)
        namehits=[v for k,v in log if k.startswith("property name")]
        if namehits: left += [(c["clone_name"],"contact property",n) for n in namehits]

        acts=[l for l in log if not l[0].startswith("property name")]
        if acts:
            print(f"\n{c['clone_name']}")
            for k,v in acts: print(f"   {k}: {str(v)[:90]}")
        if changed or acts:
            if go:
                r=call("PATCH",f"/marketing/v3/forms/{c['clone_id']}",body)
                print("   saved" if r else "   FAILED")
    print("\n" + "="*70)
    print("NOT CHANGEABLE ON THE FORM (reported, not touched):")
    seen=set()
    for name,kind,v in left:
        if (kind,v) in seen: continue
        seen.add((kind,v))
        print(f"   [{kind}] {v[:80]}")
    if not go: print("\nDRY RUN -- pass --go to apply")

if __name__=="__main__": main()
