import json,re,subprocess,html,sys
ids=json.load(open('reference/hubspot_ids.json'))
pages=[p for p in ids['pages'] if p['slug'] not in ('pl-module-library','pl-global-blocks') and not (p['slug'] or '').startswith('-temporary')]
CAT=['aging','cognitive','detox','energy','fitness','heart-health','herbal','immune-support','joint-support','mens-health','multivitamin','pediatric','prenatal','probiotics','sleep','weight-management','womens-health']
def fetch(slug):
    u='https://www.praxerasupplements.com/'+slug
    r=subprocess.run(['curl','-sS','-m','40','--cacert','/root/.ccr/ca-bundle.crt','-w','\n%{http_code}','-o','-',u],capture_output=True,text=True)
    body,_,code=r.stdout.rpartition('\n'); return code.strip(),body
def txt(h):
    h=re.sub(r'<(script|style)[^>]*>.*?</\1>',' ',h,flags=re.S|re.I); h=re.sub(r'<[^>]+>',' ',h); return re.sub(r'\s+',' ',html.unescape(h))
out=[]
for p in pages:
    slug=p['slug'] or ''
    code,h=fetch(slug); t=txt(h); tl=t.lower()
    row={'slug':slug or '(home)','http':code,'chars':len(t)}
    if code!='200': out.append(row); continue
    row['davinci_text']=len(re.findall(r'davinci',tl))
    row['davinci_links']=sorted(set(re.findall(r'href="(https?://[^"]*davincilabs[^"]*)"',h)))
    row['manufactur']=len(re.findall(r'\bwe (?:manufactur|produce)|our (?:facilit|manufactur)',tl))
    row['custom_formulation']=('custom formulation' in tl)
    row['placeholder']=bool(re.search(r'\[placeholder|in-demand|in demand',tl))
    row['fda_box']=('these statements have not been evaluated' in tl)
    row['fda_star']=bool(re.search(r'\*\s*these statements have not been evaluated',tl))
    row['dev_by_us']=('developed by us' in tl)
    row['tested_ingredients']=('and tested ingredients' in tl)
    db=re.findall(r'daily best(.{0,3})',t,flags=re.I); row['daily_best']={'®':sum(1 for x in db if '®' in x),'™':sum(1 for x in db if '™' in x),'none':sum(1 for x in db if '®' not in x and '™' not in x)} if db else None
    row['sticky']=bool(re.search(r'hs_cos_wrapper_global_header\s*\{[^}]*position:\s*sticky',h))
    if slug in CAT:
        m=re.search(r"(praxera'?s|our|real praxera)\s+[a-z’'\- ]{2,40}formulations available for private label",tl)
        row['formblock']=m.group(0)[:80] if m else None
        row['formblock_ok']=bool(m and m.group(0).startswith("praxera") and 'a selection of our existing' in tl and 'schedule a consultation' in tl)
    if slug=='fitness':
        row['vegan']=('vegan' in tl); row['vitc_card']=bool(re.search(r'vitamin c[^.]{0,40}b-?complex',tl))
    if slug=='':
        m=re.search(r'<a[^>]*href="([^"]*)"[^>]*>\s*(?:<[^>]+>\s*)*and more',h,flags=re.I); row['and_more_href']=m.group(1) if m else ('text-only' if 'and more' in tl else 'absent')
    out.append(row); print(slug or '(home)',code,file=sys.stderr)
json.dump(out,open('/tmp/claude-0/-home-user-Claude/0f427e52-eb7f-5b23-8772-a7e122ea7371/scratchpad/live_pages.json','w'),indent=1)
print('done',len(out))
