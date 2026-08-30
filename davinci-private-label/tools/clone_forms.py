"""Clone the private-label forms under Praxera names. Nothing existing is touched.

Every clone is a NEW form. The originals keep their ids, their embeds, their
submissions and their workflow enrolments -- a clone cannot disturb them, which
is what makes this safe to run while the old site is still live. The clones are
not embedded anywhere and nothing enrols on them until someone wires them up.

Two forms are deliberately skipped: the ones whose own names say DO NOT USE and
Old/Unused. Cloning a form the team has already retired just moves the confusion.
"""
import json,os,re,sys,urllib.request,urllib.error

T=os.environ["TOKEN"]
def call(m,u,body=None):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    d=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(u,data=d,method=m,
        headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
    try: return json.load(urllib.request.urlopen(r,timeout=60))
    except urllib.error.HTTPError as e:
        print("   HTTP",e.code,e.read().decode()[:400]); return None

# source id -> the name its Praxera clone should carry
PLAN = {
 "e0762402-c1e2-4a5a-8878-6441568fee67":"Praxera - Schedule a Consultation (Ads pages)",
 "0a6cdaa2-8b4a-4230-b5e7-f87c063fe6ca":"Praxera - Our Design Services",
 "b84800a2-de07-4875-9641-0a38c12eb230":"Praxera - Onboarding Guide",
 "8361c2ac-468c-4d5a-8bad-07cd8909c840":"Praxera - Contact Us",
 "824d9d5c-a5e4-4e36-9704-fd733cf4db30":"Praxera - Request a Quote",
 "1c42b9c4-2fba-4099-98a4-60116cd6764f":"Praxera - Main Lead Form",
 "2b0e60b3-03f3-427f-ae69-35513ab96b2f":"Praxera - Ingredients, Testing & Certification Guide",
 "82f30fc3-0740-411c-a3b4-13a1f9b1814a":"Praxera - Client Onboarding Guide",
 "c3728140-7dde-42d6-87cf-def58820ee74":"Praxera - Supplements Guide",
 "c53ef621-83e9-42a6-ae6a-a74b9e4317d5":"Praxera - Main Lead Form (legacy field set)",
 "dcb3c62c-8ef4-4f60-afd6-677d3a6f4348":"Praxera - Ingredients & Testing Guide (page form)",
}
SKIP = {
 "d5f7980e-bee8-40ab-8596-b20ced7704ff":"named DO NOT USE",
 "cef867f3-1e84-44aa-b251-b0644a7e345d":"named Old/Unused",
 "d8dfdd90-98f1-4cba-bedf-181dd9286ca1":"already Praxera-named, in use on 23 pages",
}
# Only the id is server-owned on create. createdAt looks like it should be too, but
# the endpoint rejects the payload without it, so it is passed through and HubSpot
# overwrites it on the new record.
STRIP = ("id","archived","createdById","updatedById")

def clean_copy(text):
    """Take DaVinci out of copy the form itself renders."""
    if not isinstance(text,str): return text
    t=re.sub(r"\bDaVinci Laboratories\b","Praxera",text)
    t=re.sub(r"\bDaVinci Labs\b","Praxera",t)
    t=re.sub(r"\bDaVinci\b","Praxera",t)
    return t

def scrub(node):
    if isinstance(node,dict):
        return {k:(clean_copy(v) if k in ("value","label","richText","placeholder",
                                          "helpText","submitButtonText","description")
                   else scrub(v)) for k,v in node.items()}
    if isinstance(node,list): return [scrub(x) for x in node]
    return node

def main():
    dry = "--go" not in sys.argv
    print("DRY RUN -- pass --go to create\n" if dry else "CREATING CLONES\n")
    out=[]
    for sid,newname in PLAN.items():
        src=call("GET",f"/marketing/v3/forms/{sid}")
        if not src: print(f"!! could not read {sid}"); continue
        body={k:v for k,v in src.items() if k not in STRIP}
        body=scrub(body)
        body["name"]=newname
        print(f"{src['name'][:52]:54} -> {newname}")
        if dry: continue
        new=call("POST","/marketing/v3/forms",body)
        if new:
            out.append({"source_id":sid,"source_name":src["name"],
                        "clone_id":new["id"],"clone_name":new["name"]})
            print(f"   created {new['id']}")
    print("\nSKIPPED:")
    for sid,why in SKIP.items(): print(f"   {sid}  {why}")
    if out:
        json.dump(out,open("reference/praxera_form_clones.json","w"),indent=1)
        print(f"\ncreated {len(out)} clones -> reference/praxera_form_clones.json")

if __name__=="__main__": main()
