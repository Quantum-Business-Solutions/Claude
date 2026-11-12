#!/usr/bin/env python3
"""Build the section files for an interactive Client Command sign-off page.

Input  : content.json  {"meta": {brand,title,intro,questions:[{g,t}]},
                         "rows": [{g,id,n,u,f,qa:[[question,answer],...]}]}
         (g = group key, f = freshness note or "", answers may contain [CONFIRM: ...])
Output : out/app.html, out/data_NN.html (<=18 KB each), out/meta.html, out/boot.html, out/full.html
Usage  : python3 build.py content.json out/
Then   : upload each file as one section of an HTML sectioned page (see README.md).
"""
import json, sys, os, glob

content = json.load(open(sys.argv[1])); out = sys.argv[2]; here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(out, exist_ok=True)
ids = [r["id"] for r in content["rows"]]; assert len(ids) == len(set(ids)), "duplicate row ids"
for r in content["rows"]:
    assert r["qa"], f"{r['n']} has no FAQs"
chunks, cur, size = [], [], 0
for r in content["rows"]:
    n = len(json.dumps(r, ensure_ascii=False))
    if size + n > 18000 and cur: chunks.append(cur); cur, size = [], 0
    cur.append(r); size += n
chunks.append(cur)
for i, c in enumerate(chunks, 1):
    open(f"{out}/data_{i:02d}.html", "w").write('<script type="application/json" class="faqdata">' + json.dumps(c, ensure_ascii=False).replace("</", "<\\/") + "</script>")
shim = "<script>try{window.localStorage.getItem('x')}catch(e){try{Object.defineProperty(window,'localStorage',{value:{getItem:function(){return null},setItem:function(){}},configurable:true})}catch(e2){}}</script>"
open(f"{out}/meta.html", "w").write('<script type="application/json" id="meta">' + json.dumps(content["meta"], ensure_ascii=False) + "</script>" + shim)
for f in ("app.html", "boot.html"):
    open(f"{out}/{f}", "w").write(open(f"{here}/template/{f}").read())
parts = [open(f"{out}/app.html").read()] + [open(f) .read() for f in sorted(glob.glob(f"{out}/data_*.html"))] + [open(f"{out}/meta.html").read(), open(f"{out}/boot.html").read()]
open(f"{out}/full.html", "w").write("<!doctype html><meta charset=utf-8><body style=margin:0>" + "\n".join(parts))
print(len(content["rows"]), "rows,", sum(len(r["qa"]) for r in content["rows"]), "FAQs,", len(chunks), "data sections")
