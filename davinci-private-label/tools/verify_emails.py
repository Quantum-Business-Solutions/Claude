"""Per-email health across the 111 Praxera clones.

Reads the widgets and flex-area sections, not content.html -- content.html does
not persist on these records, so an audit that reads it finds nothing wrong with
an email that is entirely wrong.

Three separate measures, because conflating them is how a scan reports 105
broken emails that are mostly fine:

  copy    visible words a reader sees. Strips tag attributes first, so a brand
          name inside an image filename or a hostname never counts as copy.
  links   href targets a reader can click. A Praxera email pointing at
          DaVinci's Instagram is a real defect; an image served off the DaVinci
          file domain is not, it is just where the portal keeps its files.
  hosting assets served from a DaVinci or PetTechLabs domain. Invisible today,
          but they break if that domain is disconnected at cutover.
"""
import json,re,collections,html
exec(open('/tmp/hs.py').read())

SEP=r"(?:\s|&nbsp;|&#160;| )+"
BRAND=re.compile("DaVinci"+SEP+"Laboratories"+SEP+"of"+SEP+"Vermont"
    "|DaVinci"+SEP+"Laboratories|DaVinci"+SEP+"Labs|DaVinci",re.I)
# The gap excludes : and ; so the pattern cannot jump a list colon -- without
# that, "we offer: Doctor-Formulated Supplements" reads as a manufacturing claim.
CLAIM=re.compile(r"\b(we|our)\b[^.:;<]{0,50}\b(manufactur\w*|produce|bottling|bottle[sd]?|"
                 r"formulate[sd]?|blend[s]?|encapsulat\w*)\b",re.I)
FOREIGN=re.compile(r"(davincilabs?|davinci-?lab\w*|pettechlabs|vetriscience)",re.I)

def page(path,q=None):
    out=[];q=dict(q or {});q["limit"]=100;after=None
    while True:
        if after:q["after"]=after
        d=call("GET",path,q=q);out+=d.get("results",[])
        after=(d.get("paging") or {}).get("next",{}).get("after")
        if not after:break
    return out

COPY_KEYS={"html","value","text","heading","subheading","body_text","content",
           "label_text","button_text","preview_text","plain_text"}
LINK_KEYS={"url","href","link","destination"}

def walk(node,copy,links,imgs):
    """Collect copy, link targets and image sources by key, not by regex.

    Keying on the field name is what separates a brand name a reader sees from
    one that only exists inside a filename -- a distinction a regex over the
    whole payload cannot make, and the reason an earlier pass reported 105
    broken emails that were not broken.
    """
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
    """Words a reader sees: tags stripped from the copy-bearing fields only."""
    s=" ".join(chunks)
    # hrefs live inside the copy html too; drop tags whole so their attribute
    # values never reach the text
    s=re.sub(r"<[^>]*>"," ",s)
    return re.sub(r"\s+"," ",html.unescape(s))

def hrefs(blob):
    out=set()
    for pat in (r'href=\\?"([^"\\]+)', r'"(?:url|link|href|destination)"\s*:\s*"([^"]+)"'):
        out|=set(re.findall(pat,blob))
    return {u for u in out if u.startswith("http")}

rows=[]
for e in page("/marketing/v3/emails/"):
    if "praxera" not in e["name"].lower(): continue
    d=call("GET",f"/marketing/v3/emails/{e['id']}")
    c=d.get("content") or {}
    copy=[];links=set();imgs=set()
    walk({"w":c.get("widgets"),"f":c.get("flexAreas")},copy,links,imgs)
    txt=visible(copy)
    # links also hide inside the copy html itself
    links|={u for u in re.findall(r'href="(http[^"]+)"'," ".join(copy))}
    frm=d.get("from") or {}
    rows.append({"id":e["id"],"name":e["name"],"state":d.get("state"),
        "subject":(d.get("subject") or "")[:120],
        "copy_brand":sorted({m.group(0) for m in BRAND.finditer(txt)}),
        "brand_links":sorted(u for u in links if FOREIGN.search(u)),
        "foreign_images":sorted(u for u in imgs if FOREIGN.search(u)),
        "claims":sorted({m.group(0).strip()[:80] for m in CLAIM.finditer(txt)}),
        "reply_to":frm.get("replyTo")})
json.dump(rows,open("reference/email_clones.json","w"),indent=1)

n=len(rows)
cnt=lambda k:sum(1 for r in rows if r[k])
print(f"{n} Praxera emails | non-draft {sum(1 for r in rows if r['state']!='DRAFT')}")
print(f"  DaVinci in visible copy   : {cnt('copy_brand')} emails")
print(f"  DaVinci/PTL clickable link: {cnt('brand_links')} emails")
print(f"  assets on a foreign domain: {cnt('foreign_images')} emails")
print(f"  first-person mfg claims   : {cnt('claims')} emails")
print("  reply-to:",collections.Counter(r["reply_to"] for r in rows).most_common())
lk=collections.Counter(u for r in rows for u in r["brand_links"])
print("  most common brand links:")
for u,k in lk.most_common(8): print(f"    x{k:<4} {u[:96]}")
cp=collections.Counter(s for r in rows for s in r["copy_brand"])
print("  brand strings in copy:",cp.most_common(6))
