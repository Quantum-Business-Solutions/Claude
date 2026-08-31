"""Copy-level health of the 62 Praxera pages and 75 Praxera blog posts.

Same three-way split as the email audit -- copy, links, hosting -- because the
same confusion applies: a DaVinci string in a stylesheet href is not a page
that says DaVinci.

Reads the draft, not the base record. Every change in this migration was made
to the draft, so the base record still shows the pre-migration page.
"""
import json,re,html,collections
exec(open('/tmp/hs.py').read())

SEP=r"(?:\s|&nbsp;|&#160;| )+"
BRAND=re.compile("DaVinci"+SEP+"Laboratories"+SEP+"of"+SEP+"Vermont"
    "|DaVinci"+SEP+"Laboratories|DaVinci"+SEP+"Labs|DaVinci",re.I)
CLAIM=re.compile(r"\b(we|our)\b[^.:;<]{0,50}\b(manufactur\w*|produce|bottling|bottle[sd]?|"
                 r"formulate[sd]?|blend[s]?|encapsulat\w*)\b",re.I)
FOREIGN=re.compile(r"(davincilabs?|davinci-?lab\w*|pettechlabs|vetriscience)",re.I)
PLACE=re.compile(r"\[(?:PLACEHOLDER[^\]]*|BRAND_TBD|New Brand|Brand TBD)\]",re.I)
COPY_KEYS={"html","value","text","heading","subheading","body_text","content",
           "label_text","button_text","preview_text","plain_text","post_body"}
LINK_KEYS={"url","href","link","destination"}

def walk(node,copy,links,imgs):
    if isinstance(node,dict):
        for k,v in node.items():
            if isinstance(v,str):
                if k in COPY_KEYS: copy.append(v)
                elif k in LINK_KEYS and v.startswith("http"): links.add(v)
                elif k=="src" and v.startswith("http"): imgs.add(v)
            else: walk(v,copy,links,imgs)
    elif isinstance(node,list):
        for v in node: walk(v,copy,links,imgs)

def visible(chunks):
    s=re.sub(r"<[^>]*>"," "," ".join(chunks))
    return re.sub(r"\s+"," ",html.unescape(s))

def page(path):
    out=[];q={"limit":100};after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

def audit(records,draft_path,label):
    rows=[]
    for r in records:
        d=call("GET",draft_path.format(id=r["id"]))
        copy=[];links=set();imgs=set()
        # widgets/layoutSections hold the real content; the rest is chrome
        walk({k:d.get(k) for k in ("widgets","layoutSections","widgetContainers",
                                   "postBody","htmlTitle","metaDescription")},copy,links,imgs)
        txt=visible(copy)
        links|=set(re.findall(r'href="(http[^"]+)"'," ".join(copy)))
        rows.append({"id":r["id"],"slug":r.get("slug"),"name":r.get("name"),
            "state":d.get("currentState"),
            "copy_chars":len(txt),
            "copy_brand":sorted({m.group(0) for m in BRAND.finditer(txt)}),
            "brand_links":sorted(u for u in links if FOREIGN.search(u)),
            "foreign_images":sorted(u for u in imgs if FOREIGN.search(u)),
            "claims":sorted({m.group(0).strip()[:80] for m in CLAIM.finditer(txt)}),
            "placeholders":sorted({m.group(0) for m in PLACE.finditer(txt)}),
            "bare_none":len(re.findall(r"(?<![A-Za-z])None(?![A-Za-z])",txt))})
    json.dump(rows,open(f"reference/{label}.json","w"),indent=1)
    cnt=lambda k:sum(1 for r in rows if r[k])
    print(f"\n{label}: {len(rows)} records | published "
          f"{sum(1 for r in rows if r['state']=='PUBLISHED')}")
    print(f"  DaVinci in visible copy   : {cnt('copy_brand')}")
    print(f"  DaVinci clickable link    : {cnt('brand_links')}")
    print(f"  assets on foreign domain  : {cnt('foreign_images')}")
    print(f"  first-person mfg claims   : {cnt('claims')}")
    print(f"  unreplaced placeholders   : {cnt('placeholders')}")
    print(f"  literal word 'None'       : {cnt('bare_none')}")
    print(f"  empty copy (0 chars)      : {sum(1 for r in rows if r['copy_chars']==0)}")
    return rows

pages=[p for p in page("/cms/v3/pages/site-pages")
       if "praxera" in (p.get("url") or "").lower()]
audit(pages,"/cms/v3/pages/site-pages/{id}/draft","page_health")

posts=[b for b in page("/cms/v3/blogs/posts")
       if "praxera" in ((b.get("url") or "")+(b.get("slug") or "")).lower()]
audit(posts,"/cms/v3/blogs/posts/{id}/draft","blog_health")
