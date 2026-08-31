"""Build the per-asset sign-off page for the ClientCommand portal.

This replaces the Claude artifact version. The artifact needed a Claude account
to open and its state never reached ClientCommand, so 272 client approvals
would have been unrecoverable. The portal route is /portal/<share_token> and
the sign-offs land in portal_document_state where they can be queried.

Whole document rather than sections: this is an application, not a document,
and the section renderer would inject a heading into the middle of it.
"""
import json,re,datetime

rows=json.load(open("reference/ledger_rows.json"))
redir=json.load(open("reference/redirects.json"))
rows["redirects"]={"pairs":redir["counts"]["redirects"],
                   "by_kind":redir["counts"]["by_kind"]}
# The same handful of issue labels repeat across hundreds of rows ("manufacturing
# claim", "assets off-domain", "DaVinci reply-to"). Interning them into a lookup
# is worth about a third of the payload, and the payload has to be pasted
# through a tool call by hand, where every kilobyte is a chance to mistype.
labels=[]; idx={}
for r in rows["rows"]:
    out=[]
    for kind,text in r["i"]:
        key=(kind,text)
        if key not in idx:
            idx[key]=len(labels); labels.append([kind,text])
        out.append(idx[key])
    r["i"]=out
rows["labels"]=labels
# One row per line. The payload is pasted through a tool call by hand, and a
# single 52KB line is a single point of failure; line-structured JSON keeps any
# slip local and makes it visible on inspection rather than only at parse time.
def _pack(o):
    parts=[]
    parts.append('{"stamp":'+json.dumps(o["stamp"])+",")
    parts.append('"groups":'+json.dumps(o["groups"],separators=(",",":"))+",")
    parts.append('"redirects":'+json.dumps(o["redirects"],separators=(",",":"))+",")
    parts.append('"labels":'+json.dumps(o["labels"],separators=(",",":"))+",")
    parts.append('"rows":[')
    parts.append(",\n".join(json.dumps(r,separators=(",",":")) for r in o["rows"]))
    parts.append("]}")
    return "\n".join(parts)
DATA=_pack(rows).replace("<","\\u003c")
JS=open("src/signoff.js").read()
CSS=re.sub(r"/\*.*?\*/","",open("src/review.css").read(),flags=re.S)
CSS=re.sub(r"\n{2,}","\n",CSS).strip()

assert "</script" not in JS and "</script" not in DATA

doc=('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
 '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
 "<title>Praxera Asset Sign-off</title>\n"
 '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:'
 'opsz,wght@6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:'
 'wght@400;500;600&display=swap">\n'
 f"<style>{CSS}</style>\n</head><body>\n"
 '<div id="root"></div>\n'
 f'<script type="application/json" id="data">{DATA}</script>\n'
 f"<script>{JS}</script>\n</body></html>\n")

open("deliverables/signoff_portal.html","w").write(doc)
n=len(rows["rows"])
print(f"{len(doc)} bytes | {n} rows |",
      {g[0]:sum(1 for r in rows["rows"] if r["k"]==g[0]) for g in rows["groups"]})
