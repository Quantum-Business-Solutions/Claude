"""Clone the live core private-label workflows into disabled Praxera copies.

Every clone is created with isEnabled false and stays that way. That is the
whole point of the parallel-stack approach: the Praxera automation exists, is
inspectable, and sends nothing, until someone flips it deliberately.

Three substitutions happen inside the copy:

  send actions   content_id -> the Praxera clone of that email, from the
                 source->clone map built when the 83 emails were cloned
  enrolment      form GUIDs -> the Praxera form clones
  identity       id, uuid, revisionId are dropped so HubSpot mints new ones

Anything the map cannot resolve is REPORTED and left pointing at the original.
A workflow that silently sends a DaVinci email is worse than one that obviously
still needs work.
"""
import json,os,re,sys,time,urllib.request,urllib.error,collections

T=os.environ["TOKEN"]
def call(m,u,body=None,tr=4):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    d=json.dumps(body).encode() if body is not None else None
    for i in range(tr):
        try:
            r=urllib.request.Request(u,data=d,method=m,
                headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
            return json.load(urllib.request.urlopen(r,timeout=90))
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            if e.code not in (429,502,503,504) or i==tr-1:
                return {"_err":e.code,"_msg":e.read().decode()[:400]}
            time.sleep(2*(i+1))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

# fields HubSpot owns; a create must not carry them
STRIP=("id","uuid","revisionId","createdAt","updatedAt","crmObjectCreationStatus")
BRAND=re.compile(r"DaVinci Laboratories|DaVinci Labs|DaVinci|DVL\s*//\s*|DV:\s*",re.I)

def rename(n):
    s=BRAND.sub("",n).strip(" -:/")
    s=re.sub(r"\s{2,}"," ",s)
    return f"Praxera - {s}"[:250]

def main():
    go="--go" in sys.argv
    M=json.load(open("reference/merged_audit.json"))
    emap={c["source_id"]:c["clone_id"] for c in json.load(open("reference/praxera_email_clones.json"))}
    fmap={c["source_id"]:c["clone_id"] for c in json.load(open("reference/praxera_form_clones.json"))}
    targets=[w for w in M["workflows"] if w["tier"]=="CORE" and w["live"]]
    print(f"{len(targets)} live core workflows   mode: {'APPLY' if go else 'DRY RUN'}\n")

    done=[]
    if os.path.exists("reference/praxera_workflow_clones.json"):
        done=json.load(open("reference/praxera_workflow_clones.json"))
    already={d["source_id"] for d in done}

    out=[]; unresolved=collections.Counter()
    for w in targets:
        if w["id"] in already: print(f"  skip (already cloned) {w['name'][:52]}"); continue
        src=call("GET",f"/automation/v4/flows/{w['id']}")
        if not src or "_err" in (src or {}):
            print(f"  !! could not read {w['name'][:46]}"); continue
        body={k:v for k,v in src.items() if k not in STRIP}
        blob=json.dumps(body)

        # emails
        ec=0
        for sid,cid in emap.items():
            if f'"content_id": "{sid}"' in blob or f'"content_id":"{sid}"' in blob:
                blob=blob.replace(f'"content_id": "{sid}"',f'"content_id": "{cid}"')
                blob=blob.replace(f'"content_id":"{sid}"',f'"content_id":"{cid}"')
                ec+=1
        # forms
        fc=0
        for sid,cid in fmap.items():
            if sid in blob: blob=blob.replace(sid,cid); fc+=1
        body=json.loads(blob)

        # anything still pointing at a non-cloned email
        sends=[a["fields"]["content_id"] for a in body.get("actions",[])
               if str(a.get("actionTypeId"))=="0-4" and a.get("fields",{}).get("content_id")]
        clones=set(emap.values())
        stray=[s for s in sends if s not in clones]
        for s in stray: unresolved[s]+=1

        body["name"]=rename(w["name"])
        body["isEnabled"]=False            # never on, no exceptions
        body["description"]=(body.get("description") or "")+\
            " [Praxera clone — staged for the brand migration. Disabled by design.]"

        print(f"  {w['name'][:46]:48} -> {body['name'][:46]:48} emails={ec} forms={fc} unmapped={len(stray)}")
        if not go: continue
        new=call("POST","/automation/v4/flows",body)
        if not new or "_err" in (new or {}):
            print(f"     FAILED {(new or {}).get('_msg','')[:200]}"); continue
        back=call("GET",f"/automation/v4/flows/{new['id']}")
        if back.get("isEnabled"):
            print("     !! CLONE CAME BACK ENABLED — disabling"); 
            call("PATCH",f"/automation/v4/flows/{new['id']}",{"isEnabled":False})
            back=call("GET",f"/automation/v4/flows/{new['id']}")
        out.append({"source_id":w["id"],"source_name":w["name"],"clone_id":new["id"],
                    "clone_name":new["name"],"enabled":back.get("isEnabled"),
                    "emails_repointed":ec,"forms_repointed":fc,"unmapped_emails":stray})
        print(f"     created {new['id']}  enabled={back.get('isEnabled')}")

    if go and out:
        json.dump(done+out,open("reference/praxera_workflow_clones.json","w"),indent=1)
    print(f"\ncloned: {len(out)}")
    if unresolved:
        print(f"\nSEND ACTIONS WITH NO PRAXERA EMAIL ({len(unresolved)} distinct):")
        for e,n in unresolved.most_common(): print(f"   {n:>2}x  content_id {e}")

if __name__=="__main__": main()
