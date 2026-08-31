"""Build the reviewable asset ledger: every asset with an approve / needs-work
control and a comment thread.

There is no shared database available to a published artifact here, so the
review state lives in the page and the page saves new versions of ITSELF. Two
consequences shape the whole design:

  * The document has to be reconstructable from inside the page. It is, from
    four parts read back off the DOM by id -- the stylesheet, this script, the
    asset data, and the live review state -- so nothing is duplicated and the
    live DOM is never serialized.
  * A save is a real publish. They are batched behind a short debounce and
    tried through the files form first, which leaves the reviewer's view
    running; only if that form is unavailable does it fall back to the html
    form, which reloads.
"""
import json,html,re,datetime

R=lambda n:json.load(open(f"reference/{n}.json"))
redir=None
state=R("current_state"); embeds=R("form_embeds"); pairs=R("pairs")
pageh={r["slug"]:r for r in R("page_health")}
blogh={r["slug"]:r for r in R("blog_health")}
emailh={r["id"]:r for r in R("email_clones")}
wf=R("workflow_clones")
redir=R("redirects")
STAMP=datetime.date.today().strftime("%-d %B %Y")
PFX=re.compile(r"^Praxera\s*-\s*")
strip=lambda n:PFX.sub("",n or "")
host=lambda u:re.sub(r"^https?://","",u) if u else ""

rows=[]
def add(k,rid,name,replaces,issues,full="",new=False):
    r={"k":k,"id":rid,"n":name,"r":replaces,"i":issues}
    if full and full!=replaces: r["t"]=full
    if new: r["new"]=1
    rows.append(r)

# ---- pages ---------------------------------------------------------------
for p in sorted(pairs["pages"],key=lambda x:x["slug"] or ""):
    h=pageh.get(p["slug"],{}); i=[]
    if h.get("brand_links"):
        n=len(h["brand_links"]); i.append(["bad",f"{n} DaVinci link"+("s" if n>1 else "")])
    if h.get("claims"): i.append(["bad","manufacturing claim"])
    if h.get("placeholders"): i.append(["warn","placeholder copy"])
    if p["slug"] in embeds["pages_with_no_form"]: i.append(["mute","no form"])
    if h.get("foreign_images"):
        n=len(h["foreign_images"]); i.append(["mute",f"{n} asset"+("s" if n>1 else "")+" off-domain"])
    add("p",p["slug"] or "home",p["slug"] or "(home)",
        host(p["source_url"]),i,new=not p["source_url"])

# ---- blog ----------------------------------------------------------------
for b in sorted(pairs["blog"],key=lambda x:x["slug"] or ""):
    h=blogh.get(b["slug"],{}); i=[]
    if h.get("brand_links"): i.append(["bad","DaVinci link"])
    if h.get("claims"): i.append(["bad","manufacturing claim"])
    if h.get("bare_none"): i.append(["warn",'literal "None"'])
    if not b.get("tags"): i.append(["warn","no tags"])
    if (b.get("publishDate") or "").startswith("1970"): i.append(["warn","1970 date"])
    src=host(b["source_url"])
    seg=src.split("/")
    short=(seg[0]+"/\u2026/"+seg[-1]) if len(seg)>2 else src
    add("b",b["slug"],(b["name"] or "")[:88],short,i,src,new=not b["source_url"])

# ---- emails --------------------------------------------------------------
for e in sorted(pairs["emails"],key=lambda x:x["name"]):
    h=emailh.get(e["id"],{}); i=[]
    if h.get("brand_links"):
        n=len(h["brand_links"])
        i.append(["bad",f"{n} DaVinci social link"+("s" if n>1 else "")])
    if h.get("claims"): i.append(["bad","manufacturing claim"])
    if h.get("reply_to")=="enews@davincilabs.com": i.append(["warn","DaVinci reply-to"])
    if h.get("foreign_images"): i.append(["mute","assets off-domain"])
    add("e",str(e["id"]),strip(e["name"])[:84],(e["source_name"] or "new for Praxera")[:72],i)

# ---- forms ---------------------------------------------------------------
for f in sorted(state["praxera_forms"],key=lambda x:x["name"]):
    n=f["name"].strip()
    on=[x or "(home)" for x in embeds["by_form"].get(n,[])]
    used=sum(1 for w in wf for x in w["enrol_forms"] if x["id"]==f["id"])
    i=[] if on else [["bad","on no page"]]
    if used: i.append(["mute",f"{used} flow"+("s" if used>1 else "")+" enrol on it"])
    add("f",f["id"],n,
        (f"on {len(on)} page"+("s" if len(on)>1 else "")+": "+", ".join(sorted(on)[:5])
         +(" …" if len(on)>5 else "")) if on else "on no page",i)

# ---- workflows -----------------------------------------------------------
for f in sorted(wf,key=lambda x:-x["sends"]):
    bad=sorted({x["name"] for x in f["enrol_forms"] if not x["praxera"]})
    i=[]
    if f["davinci_sends"]: i.append(["bad",f'{f["davinci_sends"]} DaVinci send'])
    if bad: i.append(["bad","enrols on "+", ".join(bad[:2])])
    if not f["enrol_forms"]: i.append(["warn","no form enrolment"])
    if f["dead_workflow_list_clauses"]:
        n=f["dead_workflow_list_clauses"]
        i.append(["mute",f"{n} dead clause"+("s" if n>1 else "")])
    add("w",str(f["id"]),strip(f["name"])[:70],
        f'{f["sends"]} email sends · '+("enabled" if f["enabled"] else "disabled"),i)

RD="Redirects from at cutover"
DATA={"stamp":STAMP,"rows":rows,
      "groups":[["p","Website pages",RD],["b","Blog posts",RD],
                ["e","Marketing emails","Replaces"],["f","Forms","Placement"],
                ["w","Workflows","Detail"]],
      "redirects":{"pairs":redir["counts"]["redirects"],
                   "by_kind":redir["counts"]["by_kind"],
                   "orphan_sources":[s["url"] for s in redir["orphan_sources"]],
                   "orphan_targets":redir["counts"]["orphan_targets"]}}
json.dump(DATA,open("reference/ledger_rows.json","w"),indent=1)
print("rows:",len(rows),{g:sum(1 for r in rows if r['k']==g) for g,*_ in DATA["groups"]})

# ---------------------------------------------------------------------------
# Assemble two shapes of the same page.
#
#   artifact_review.html  the body fragment the Artifact tool wants for the
#                         first publish (it supplies the skeleton itself)
#   review_standalone.html a full document, for local rendering and for the
#                         repo -- and the same shape the page rebuilds when it
#                         saves itself
# ---------------------------------------------------------------------------
CSS=open("src/review.css").read()
JS=open("src/review.js").read()
DATA_JSON=json.dumps(DATA,separators=(",",":")).replace("<","\\u003c")
REVIEW_JSON=json.dumps({"v":1,"items":{}})

FONTS=('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:'
 'opsz,wght@6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:'
 'wght@400;500;600&display=swap">\n')

def body():
    return ('<div id="root"></div>\n'
      f'<script type="application/json" id="data">{DATA_JSON}</script>\n'
      f'<script type="application/json" id="review">{REVIEW_JSON}</script>\n'
      f'<script id="app">{JS}</script>\n')

frag=("<title>Praxera Migration Asset Ledger</title>\n"+FONTS
      +f'<style id="sheet">{CSS}</style>\n'+body())
full=('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
      '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
      "<title>Praxera Migration Asset Ledger</title>\n"+FONTS
      +f'<style id="sheet">{CSS}</style>\n</head><body>\n'+body()+"</body></html>\n")

open("deliverables/artifact_review.html","w").write(frag)
open("deliverables/review_standalone.html","w").write(full)
print("fragment  ",len(frag),"bytes")
print("standalone",len(full),"bytes")
assert "</script" not in JS, "the app script would terminate itself when re-embedded"
assert "</script" not in DATA_JSON
