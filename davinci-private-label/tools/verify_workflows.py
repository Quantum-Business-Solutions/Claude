"""Read the 12 Praxera flows and report what they send, what enrols, what is dead.

Counting send actions rather than trusting the clone log: a flow that still
points one send at a DaVinci email would look identical from the outside.

The send action is actionTypeId 0-4 and the email lives in fields.content_id --
snake_case, unlike almost everything else in the v4 flow payload.
"""
import json,re,collections
exec(open('/tmp/hs.py').read())

st=json.load(open("reference/current_state.json"))
def page(path):
    out=[];q={"limit":100};after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

emails={str(e["id"]):e["name"] for e in page("/marketing/v3/emails/")}
forms={f["id"]:f["name"].strip() for f in page("/marketing/v3/forms/")}
ispx=lambda n:"praxera" in (n or "").lower()

def formids(o):
    """Every formId under an arbitrary slice of the flow payload."""
    s=json.dumps(o)
    return sorted(set(re.findall(r'"formId"\s*:\s*"([0-9a-f-]{36})"',s)))

rows=[]
for w in st["praxera_workflows"]:
    f=call("GET",f"/automation/v4/flows/{w['id']}")
    sends=[a["fields"]["content_id"] for a in f.get("actions",[])
           if a.get("actionTypeId")=="0-4" and a.get("fields",{}).get("content_id")]
    known=[s for s in sends if s in emails]
    px=[s for s in known if ispx(emails[s])]
    dv=[s for s in known if not ispx(emails[s])]
    enrol=formids(f.get("enrollmentCriteria"))
    branch=[i for i in formids(f.get("actions")) if i not in enrol]
    dead=len(re.findall(r'"inListType"\s*:\s*"WORKFLOWS_',json.dumps(f)))
    rows.append({"id":w["id"],"name":w["name"],"enabled":f.get("isEnabled"),
        "sends":len(sends),"unknown_email_ids":[s for s in sends if s not in emails],
        "praxera_sends":len(px),"davinci_sends":len(dv),
        "davinci_send_names":sorted({emails[s] for s in dv}),
        "enrol_forms":[{"id":i,"name":forms.get(i,"(deleted)"),"praxera":ispx(forms.get(i))} for i in enrol],
        "branch_forms":[{"id":i,"name":forms.get(i,"(deleted)"),"praxera":ispx(forms.get(i))} for i in branch],
        "dead_workflow_list_clauses":dead,
        "suppression_lists":len(f.get("suppressionListIds") or [])})
json.dump(rows,open("reference/workflow_clones.json","w"),indent=1)

tot=sum(r["sends"] for r in rows); px=sum(r["praxera_sends"] for r in rows)
dv=sum(r["davinci_sends"] for r in rows)
ef=sum(len(r["enrol_forms"]) for r in rows); efp=sum(sum(1 for x in r["enrol_forms"] if x["praxera"]) for r in rows)
print(f"{len(rows)} flows | enabled {sum(1 for r in rows if r['enabled'])} "
      f"| sends {tot}: {px} Praxera / {dv} DaVinci "
      f"| enrolment forms {efp}/{ef} Praxera "
      f"| dead workflow-list clauses {sum(r['dead_workflow_list_clauses'] for r in rows)}")
for r in sorted(rows,key=lambda x:-x["sends"]):
    e=r["enrol_forms"]; n=len(e); p=sum(1 for x in e if x["praxera"])
    flag=""
    if r["davinci_sends"]: flag+=f"  !! {r['davinci_sends']} DaVinci sends"
    if n and p<n: flag+=f"  !! {n-p} non-Praxera enrolment form(s)"
    if not n: flag+="  !! no form enrolment"
    print(f"  {r['sends']:>3} sends  enrol {p}/{n}  dead {r['dead_workflow_list_clauses']}  "
          f"{'ON' if r['enabled'] else 'off'}  {r['name'][:56]}{flag}")
