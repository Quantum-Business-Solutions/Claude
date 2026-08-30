"""Pull the old asset and its Praxera replacement side by side, so copy can be compared.

A migration list tells you what exists. It does not tell you whether the new page
actually says what the old one said, and that is the question on a client call --
did the value proposition survive the rebrand, or did a paragraph quietly vanish?

So for each mapped pair this pulls the page title, the meta description, the H1
and the opening body paragraph from BOTH sides. Where the new side is blank, the
replacement has not been written yet, and that is the finding.
"""
import json,os,re,time,urllib.request,urllib.error,html
import concurrent.futures as cf

T=os.environ["TOKEN"]
def get(u,tr=4):
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

TAGS=re.compile(r"<[^>]+>")
def text(s,limit=340):
    s=TAGS.sub(" ",s or "")
    s=html.unescape(s)
    s=re.sub(r"\s+"," ",s).strip()
    return s[:limit]

def first_para(blob):
    """The first real sentence of body copy, skipping nav and one-word cells."""
    for m in re.finditer(r"<p[^>]*>(.*?)</p>",blob,re.S|re.I):
        t=text(m.group(1),400)
        if len(t)>70 and not t.lower().startswith(("copyright","privacy")): return t
    for m in re.finditer(r'"(?:value|html|content)"\s*:\s*"((?:[^"\\]|\\.){120,})"',blob):
        t=text(m.group(1).encode().decode("unicode_escape","ignore"),400)
        if len(t)>70: return t
    return ""

def h1(blob):
    m=re.search(r"<h1[^>]*>(.*?)</h1>",blob,re.S|re.I)
    return text(m.group(1),200) if m else ""

def snapshot(kind,pid):
    ep={"site":"/cms/v3/pages/site-pages","landing":"/cms/v3/pages/landing-pages",
        "blog":"/cms/v3/blogs/posts"}[kind]
    d=get(f"{ep}/{pid}/draft") or get(f"{ep}/{pid}")
    if not d: return None
    blob=json.dumps(d)
    return {"name":d.get("name",""),"title":d.get("htmlTitle",""),
            "meta":d.get("metaDescription","") or "",
            "h1":h1(blob),"para":first_para(blob),
            "state":d.get("state",d.get("currentState","")),
            "url":d.get("url","") or d.get("absoluteUrl","")}

def main():
    M=json.load(open("reference/merged_audit.json"))
    idx=json.load(open("reference/page_index.json"))
    newby={p["slug"]:p["id"] for p in idx["production"]}
    umap=json.load(open("reference/url_map.json"))
    assets={a["Live URL"].split("?")[0]:a for a in M["patrick_assets_rechecked"]}

    pairs=[]
    for r in umap:
        if not r.get("new"): continue
        old=assets.get(r["old"])
        newslug=r["new"].replace("https://www.praxerasupplements.com/","")
        nid=newby.get(newslug)
        if not nid: continue
        pairs.append((r,old,nid,newslug))

    def work(p):
        r,old,nid,newslug=p
        row={"old_url":r["old"],"new_url":r["new"],"emails":r["emails"],
             "confidence":r["confidence"],"new_slug":newslug}
        if old and old.get("HubSpot ID") and old["Asset Type"]!="Main-site page":
            kind={"Blog post":"blog","Landing page":"landing","Site page":"site"}[old["Asset Type"]]
            row["old"]=snapshot(kind,old["HubSpot ID"]) or {"name":old["Title"],
                "title":"","meta":"","h1":"","para":"","state":"GONE","url":r["old"]}
            row["old_type"]=old["Asset Type"]
        else:
            row["old"]={"name":(old or {}).get("Title","(main site, not in HubSpot)"),
                        "title":"","meta":"","h1":"","para":"",
                        "state":"NOT IN HUBSPOT","url":r["old"]}
            row["old_type"]="Main-site page"
        row["new"]=snapshot("site",nid) or {}
        return row

    with cf.ThreadPoolExecutor(5) as ex:
        rows=list(ex.map(work,pairs))
    rows.sort(key=lambda x:-x["emails"])
    json.dump(rows,open("reference/compare_pairs.json","w"),indent=1)
    print(f"pairs compared: {len(rows)}\n")
    for r in rows:
        print(f"[{r['emails']:>3} emails] {r['old_type']}")
        print(f"   OLD {r['old']['state']:16} {r['old']['name'][:60]}")
        print(f"       h1  : {r['old']['h1'][:88]}")
        print(f"       copy: {r['old']['para'][:88]}")
        print(f"   NEW {r['new'].get('state','?'):16} {r['new'].get('name','')[:60]}")
        print(f"       h1  : {r['new'].get('h1','')[:88]}")
        print(f"       copy: {r['new'].get('para','')[:88]}\n")

if __name__=="__main__": main()
