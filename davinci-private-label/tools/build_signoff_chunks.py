"""Emit the sign-off page as section-sized chunks.

The payload has to cross into ClientCommand through a tool call written out by
hand. At 76KB in one piece that is a single point of failure: one wrong
character inside a 52KB JSON island and the page parses to nothing, on a page a
client is meant to sign off in. Split across sections instead -- each write
returns its own body_chars, so a bad chunk is identified and re-sent on its own
rather than taking the page down with it.

The app reads every #data-N island it finds and concatenates the rows, so the
number of chunks is free to change without touching the script.
"""
import json,re,math

rows=json.load(open("reference/ledger_rows.json"))
redir=json.load(open("reference/redirects.json"))
labels=[];idx={}
for r in rows["rows"]:
    out=[]
    for kind,text in r["i"]:
        k=(kind,text)
        if k not in idx: idx[k]=len(labels); labels.append([kind,text])
        out.append(idx[k])
    r["i"]=out

META={"stamp":rows["stamp"],"groups":rows["groups"],"labels":labels,
      "redirects":{"pairs":redir["counts"]["redirects"],
                   "by_kind":redir["counts"]["by_kind"]}}
CSS=re.sub(r"/\*.*?\*/","",open("src/review.css").read(),flags=re.S)
CSS=re.sub(r"\n{2,}","\n",CSS).strip()
JS=open("src/signoff.js").read()

esc=lambda s:s.replace("<","\\u003c")
CHUNKS=4
per=math.ceil(len(rows["rows"])/CHUNKS)
parts=[rows["rows"][i*per:(i+1)*per] for i in range(CHUNKS)]

secs=[]
secs.append(("app","Sign-off",
  f"<style>{CSS}\nsection>h2:first-child{{display:none}}</style>\n"
  '<div id="root"></div>'))
for i,p in enumerate(parts,1):
    body=esc("[\n"+",\n".join(json.dumps(r,separators=(",",":")) for r in p)+"\n]")
    secs.append((f"data{i}",f"Data {i}",
      f'<script type="application/json" class="rowdata">{body}</script>'))
secs.append(("boot","Boot",
  f'<script type="application/json" id="meta">{esc(json.dumps(META,separators=(",",":")))}</script>\n'
  f"<script>{JS}</script>"))

json.dump([{"block_key":k,"label":l,"body":b} for k,l,b in secs],
          open("deliverables/signoff_chunks.json","w"),indent=1)

# a standalone copy that mirrors how the renderer will assemble it
prev="".join(f'<section id="{k}">\n<h2>{l}</h2>\n{b}\n</section>\n' for k,l,b in secs)
open("deliverables/signoff_preview.html","w").write(
 '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
 '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
 "<title>Praxera Asset Sign-off</title>\n"
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:'
 'opsz,wght@6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:'
 'wght@400;500;600&display=swap">\n</head><body>\n'+prev+"</body></html>\n")
for k,l,b in secs: print(f"  {k:6s} {len(b):>7,}  {l}")
print("total",sum(len(b) for _,_,b in secs))
