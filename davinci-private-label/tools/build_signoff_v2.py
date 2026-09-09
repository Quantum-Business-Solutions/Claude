"""Build the v2 Asset Sign-off page (two-stage approval, editable, commentable).

Inputs (reference/):
  pairs.json                 Praxera asset <-> DaVinci original
  hubspot_ids.json           live ids/urls/states pulled from HubSpot today
  page_health.json, blog_health.json   fresh content scan (verify_content.py)
  email_clones.json, workflow_clones.json, form_embeds.json, current_state.json
  design_sheet_v6.json       Melinda's Design Approval Sheet (types, rev, notes)
  hubspot_page_comments.json transcribed in-editor comments (seeded threads)

Outputs:
  reference/ledger_rows.json      rows + meta (also used by build_signoff_chunks.py)
  deliverables/signoff_chunks.json   sections to push with upsert_document_section
  deliverables/signoff_preview.html  local render of the assembled page
"""
import json,re,math,datetime,html
R=lambda n:json.load(open(f"reference/{n}.json"))
pairs=R("pairs"); ids=R("hubspot_ids"); sheet=R("design_sheet_v6"); hcom=R("hubspot_page_comments")
pageh={r["slug"]:r for r in R("page_health")}; blogh={r["slug"]:r for r in R("blog_health")}
emailh={str(r["id"]):r for r in R("email_clones")}; wf=R("workflow_clones"); embeds=R("form_embeds"); state=R("current_state")
PORTAL="4087538"; SITE="https://www.praxerasupplements.com"
SHARE="https://clientcommand.thequantumleap.business/portal/2a5c361066202d71fa47ee598d2bcb95/pages/94f31f00-08a7-4f9c-905e-fe4a5e6b8c7d"
STAMP=datetime.date.today().strftime("%-d %B %Y")
hs_page=lambda i:f"https://app.hubspot.com/pages/{PORTAL}/editor/{i}/content"
hs_post=lambda i:f"https://app.hubspot.com/blog/{PORTAL}/editor/{i}/content"
hs_mail=lambda i:f"https://app.hubspot.com/email/{PORTAL}/details/{i}"
hs_form=lambda i:f"https://app.hubspot.com/forms/{PORTAL}/editor/{i}/edit/form"
hs_flow=lambda i:f"https://app.hubspot.com/workflows/{PORTAL}/platform/flow/{i}/edit"
strip=lambda n:re.sub(r"^Praxera\s*-\s*","",n or "")
host=lambda u:re.sub(r"^https?://","",u) if u else ""
rows=[]
def add(k,rid,name,**kw):
    r={"k":k,"id":rid,"n":name,"r":kw.pop("r",""),"i":kw.pop("i",[])}
    for a,b in kw.items():
        if a=="slug" and b is not None: r[a]=b        # "" is the home page — keep it
        elif b not in (None,"",[],0,False): r[a]=b
    rows.append(r); return r
def health_chips(h,kind):
    i=[]
    if not h: return i
    if h.get("state")=="DRAFT": i.append(["warn","draft in HubSpot","Not published yet."])
    if h.get("brand_links"):
        i.append(["bad",f"{len(h['brand_links'])} DaVinci link"+("s" if len(h["brand_links"])>1 else ""),
                  "Links to: "+"; ".join(h["brand_links"][:6])])
    if h.get("copy_brand"): i.append(["bad","says DaVinci","Visible copy contains: "+", ".join(h["copy_brand"])])
    if h.get("claims"): i.append(["warn","first-person production wording","Phrases to check: "+" | ".join(h["claims"][:6])])
    if h.get("placeholders"): i.append(["warn","placeholder copy","Still shows: "+", ".join(h["placeholders"])])
    if h.get("bare_none"): i.append(["warn",'literal "None"',f"The word None appears {h['bare_none']}× where a value should be."])
    return i
# ---- website pages -------------------------------------------------------
hsp={(p["slug"] or ""):p for p in ids["pages"]}
sheetmap={s[0]:s for s in sheet["pages"]}
seen=set()
def seeds_for(slug):
    out=[]
    s=sheetmap.get(slug)
    if s and s[4]: out.append({"id":f"sheet:{slug}","n":"Melinda Elmadjian","at":(s[3] or "2026-09-07")+"T12:00:00-04:00","t":s[4],"src":"Design Approval Sheet v6"})
    for n,c in enumerate(x for x in hcom["comments"] if x["slug"]==slug):
        out.append({"id":f"hs:{slug}:{n}","n":c["n"],"at":c["at"],"t":c["t"],"src":"HubSpot page comment"})
    return out
for p in sorted(pairs["pages"],key=lambda x:x["slug"] or ""):
    slug=p["slug"] or ""
    hp=hsp.get(slug)
    if not hp: continue                      # deleted since 31 Aug (custom-formulation, alp/ads-custom) — not an asset any more
    seen.add(slug)
    key=slug or "home"; s=sheetmap.get(key); i=health_chips(pageh.get(slug),"page")
    if s:
        if s[2]=="✓": i.append(["ok","design rev 1 ✓","Design Approval Sheet v6: revision 1 reviewed."])
        elif s[2]: i.append(["warn","sheet: "+s[2],"Design Approval Sheet v6 status."])
    add("p",slug or "home",slug or "(home)",r=host(p["source_url"]),i=i,new=not p["source_url"],
        slug=slug,hid=str(hp["id"]),y=(s[1] if s else ("Blog landing" if slug.startswith("blog") else "Other")),sc=seeds_for(key))
for slug,hp in hsp.items():
    if slug in seen or slug in ("pl-module-library","pl-global-blocks") or slug.startswith("-temporary"): continue
    add("p",slug,slug,r="",i=health_chips(pageh.get(slug),"page")+[["mute","added since 31 Aug","Not in the original migration pair list."]],
        new=True,slug=slug,hid=str(hp["id"]),y="Thank You" if "ty-" in slug else "Other",sc=seeds_for(slug))
# ---- blog posts -----------------------------------------------------------
hsb={b["slug"]:b for b in ids["blog"]}
for b in sorted(pairs["blog"],key=lambda x:x["slug"] or ""):
    hb=hsb.get(b["slug"])
    if not hb: continue                      # the three amazon duplicates were deleted
    src=host(b["source_url"]); seg=src.split("/")
    add("b",b["slug"],(b["name"] or "")[:96],r=(seg[0]+"/…/"+seg[-1]) if len(seg)>2 else src,t=src,
        i=health_chips(blogh.get(b["slug"]),"blog"),new=not b["source_url"],slug=b["slug"],hid=str(hb["id"]),y="Blog post")
# ---- emails ---------------------------------------------------------------
for e in sorted(pairs["emails"],key=lambda x:x["name"]):
    h=emailh.get(str(e["id"]),{}); i=[]
    if h.get("brand_links"): i.append(["bad",f"{len(h['brand_links'])} DaVinci link"+("s" if len(h["brand_links"])>1 else ""),"Links to: "+"; ".join(h["brand_links"][:6])])
    if h.get("claims"): i.append(["warn","first-person production wording","Phrases to check: "+" | ".join(h["claims"][:6])])
    if h.get("reply_to")=="enews@davincilabs.com": i.append(["mute","DaVinci reply-to","Reply-to stays enews@davincilabs.com until a Praxera mailbox exists (Shawn, 8 Sep)."])
    add("e",str(e["id"]),strip(e["name"])[:90],r=(e["source_name"] or "new for Praxera")[:80],i=i,hid=str(e["id"]),
        y=("Workflow email" if " WF" in e["name"] or "WF:" in e["name"] else "Marketing email"))
# ---- forms ---------------------------------------------------------------
for f in sorted(state["praxera_forms"],key=lambda x:x["name"]):
    n=f["name"].strip(); on=[x or "(home)" for x in embeds["by_form"].get(n,[])]
    used=sum(1 for w in wf for x in w["enrol_forms"] if x["id"]==f["id"])
    i=[] if on else [["warn","on no page","No Praxera page embeds this form."]]
    if used: i.append(["mute",f"{used} flow"+("s" if used>1 else "")+" enrol on it","Workflow enrolment trigger uses this form."])
    add("f",f["id"],n,r=(f"on {len(on)} page"+("s" if len(on)>1 else "")+": "+", ".join(sorted(on)[:6])+(" …" if len(on)>6 else "")) if on else "on no page",
        i=i,hid=f["id"],y="Form")
# ---- workflows -----------------------------------------------------------
hsw={str(w["id"]):w for w in ids["workflows"]}
for f in sorted(wf,key=lambda x:-x["sends"]):
    live=hsw.get(str(f["id"]),{}); en=live.get("enabled",f["enabled"])
    bad=sorted({x["name"] for x in f["enrol_forms"] if not x["praxera"]}); i=[]
    if f["davinci_sends"]: i.append(["bad",f'{f["davinci_sends"]} DaVinci send',"Sends: "+", ".join(f["davinci_send_names"][:4])])
    if bad: i.append(["bad","enrols on "+", ".join(bad[:2]),"Enrolment trigger still names a non-Praxera form."])
    if not f["enrol_forms"]: i.append(["mute","no form enrolment","Enrolment is by list/property, not a form (left alone by decision, 8 Sep)."])
    if f["dead_workflow_list_clauses"]: i.append(["mute",f"{f['dead_workflow_list_clauses']} dead clause"+("s" if f["dead_workflow_list_clauses"]>1 else ""),"Inherited from the DaVinci original; references a list that no longer exists."])
    i.append(["mute","off" if not en else "ON","Workflow is "+("switched off — turn on at cutover." if not en else "enabled.")])
    add("w",str(f["id"]),strip(f["name"])[:80],r=f'{f["sends"]} email sends',i=i,hid=str(f["id"]),y="Workflow")
# ---- meta -----------------------------------------------------------------
META={"stamp":STAMP,"title":"Praxera asset sign-off","file":"praxera-asset-signoff",
 "brandline":"FoodScience LLC · HubSpot 4087538 · Private Label → Praxera",
 "intro":"Every Praxera page, post, email, form and workflow, with two approvals per item: QBS signs off the build, the client signs off the content. "
         "Open a row to see findings, the client's comments (from the Design Approval Sheet and HubSpot), and the history of who did what. "
         "Edit, add or remove rows as the list changes; everything is saved to the portal and shared with everyone who opens this page.",
 "note":"Several people can work at once — changes merge item by item and the page refreshes every 25 seconds.",
 "share":SHARE,
 "groups":[["p","Website pages","Redirects from at cutover"],["b","Blog posts","Redirects from at cutover"],
           ["e","Emails","Replaces"],["f","Forms","Placement"],["w","Workflows","Detail"]],
 "keys":{"p":"website-pages","b":"blog-posts","e":"emails","f":"forms","w":"workflows"},
 "hs":{"p":hs_page("{id}"),"b":hs_post("{id}"),"e":hs_mail("{id}"),"f":hs_form("{id}"),"w":hs_flow("{id}")},
 "live":{"p":SITE+"/{slug}","b":SITE+"/{slug}"}}
json.dump({"stamp":STAMP,"rows":rows,"groups":META["groups"],"meta":META},open("reference/ledger_rows.json","w"),indent=1)
print("rows:",len(rows),{g:sum(1 for r in rows if r['k']==g) for g,*_ in META["groups"]},
      "seeded comments:",sum(len(r.get("sc",[])) for r in rows),
      "findings:",sum(1 for r in rows for x in r["i"] if x[0] in("bad","warn")))
# ---- chunks -----------------------------------------------------------------
labels=[];idx={}
for r in rows:
    out=[]
    for x in r["i"]:
        k=tuple(x)
        if k not in idx: idx[k]=len(labels); labels.append(list(x))
        out.append(idx[k])
    r["i"]=out
META["labels"]=labels
types=[]
for r in rows:
    if r.get("y") and r["y"] not in types: types.append(r["y"])
    if r.get("y"): r["y"]=types.index(r["y"])
META["types"]=types
import subprocess
SCR="/tmp/claude-0/-home-user-Claude/0f427e52-eb7f-5b23-8772-a7e122ea7371/scratchpad"
JSMIN=subprocess.run(["npx","terser","src/signoff.js","--compress","--mangle","--comments","false"],cwd=".",capture_output=True,text=True,env={**__import__("os").environ,"PATH":SCR+"/node_modules/.bin:"+__import__("os").environ["PATH"]})
assert JSMIN.returncode==0,JSMIN.stderr
JS=JSMIN.stdout.strip(); open("deliverables/signoff.min.js","w").write(JS)
assert "</script" not in JS
CSS=re.sub(r"/\*.*?\*/","",open("src/review.css").read(),flags=re.S); CSS=re.sub(r"\n{2,}","\n",CSS).strip()
esc=lambda s:s.replace("<","\\u003c")
CHUNKS=4; per=math.ceil(len(rows)/CHUNKS); parts=[rows[i*per:(i+1)*per] for i in range(CHUNKS)]
secs=[("app","Sign-off",f"<style>{CSS}\nsection>h2:first-child{{display:none}}</style>\n<div id=\"root\"></div>")]
for i,p in enumerate(parts,1):
    body=esc("[\n"+",\n".join(json.dumps(r,separators=(",",":"),ensure_ascii=False) for r in p)+"\n]")
    secs.append((f"data{i}",f"Data {i}",f'<script type="application/json" class="rowdata">{body}</script>'))
# meta and boot are separate sections so each stays small enough to send by hand;
# boot (the app) must remain LAST — it reads #meta and every rowdata island.
secs.append(("meta","Meta",f'<script type="application/json" id="meta">{esc(json.dumps(META,separators=(",",":"),ensure_ascii=False))}</script>'))
secs.append(("boot","Boot",f'<script>{JS}</script>'))
json.dump([{"block_key":k,"label":l,"body":b} for k,l,b in secs],open("deliverables/signoff_chunks.json","w"),indent=1,ensure_ascii=False)
prev="".join(f'<section id="{k}">\n<h2>{l}</h2>\n{b}\n</section>\n' for k,l,b in secs)
open("deliverables/signoff_preview.html","w").write('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>Praxera Asset Sign-off</title>\n</head><body>\n'+prev+"</body></html>\n")
for k,l,b in secs: print(f"  {k:6s} {len(b):>7,}  {l}")
print("total",sum(len(b) for _,_,b in secs))
