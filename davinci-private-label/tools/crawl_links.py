import json,re,urllib.request,urllib.error,html as H
from collections import Counter,defaultdict
urls=[u.strip() for u in open('/tmp/urls.txt') if u.strip()]
def get(u):
    try:
        r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 QA'})
        with urllib.request.urlopen(r,timeout=30) as f: return f.status,f.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e: return e.code,''
    except Exception as e: return 0,''
empty=defaultdict(list); hashonly=defaultdict(list); pldemo=defaultdict(list)
davinci=defaultdict(list); alltargets=Counter(); pagestatus={}
for u in urls:
    st,s=get(u)
    pagestatus[u]=st
    if not s: continue
    for a,txt in re.findall(r'<a\b([^>]*)>(.*?)</a>',s,re.S):
        h=re.search(r'href\s*=\s*"([^"]*)"',a)
        href=h.group(1) if h else None
        t=re.sub(r'\s+',' ',H.unescape(re.sub(r'<[^>]+>','',txt))).strip()[:38]
        slug=u.replace('https://www.praxerasupplements.com/','') or '(home)'
        if href is None or href=='': empty[slug].append(t); continue
        if href=='#': hashonly[slug].append(t); continue
        if 'pl-demo' in href: pldemo[slug].append((t,href))
        if 'davinci' in href.lower(): davinci[slug].append((t,href))
        if href.startswith('/') or href.startswith('http'): alltargets[href]+=1
json.dump({'empty':{k:v for k,v in empty.items()},'hash':{k:v for k,v in hashonly.items()},
 'pldemo':{k:v for k,v in pldemo.items()},'davinci':{k:v for k,v in davinci.items()},
 'targets':dict(alltargets),'pagestatus':pagestatus},open('/tmp/crawl.json','w'))
print('pages crawled:',len(urls))
print('page statuses:',dict(Counter(pagestatus.values())))
print()
print('EMPTY href  : %d links across %d pages'%(sum(len(v) for v in empty.values()),len(empty)))
print('href="#"    : %d links across %d pages'%(sum(len(v) for v in hashonly.values()),len(hashonly)))
print('pl-demo-*   : %d links across %d pages'%(sum(len(v) for v in pldemo.values()),len(pldemo)))
print('to davinci  : %d links across %d pages'%(sum(len(v) for v in davinci.values()),len(davinci)))
