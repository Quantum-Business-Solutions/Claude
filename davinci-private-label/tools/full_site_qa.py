import json,re,urllib.request,urllib.error,html as H
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
BASE='https://www.praxerasupplements.com'
def get(u):
    try:
        r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 QA'})
        with urllib.request.urlopen(r,timeout=35) as f: return f.status,f.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e: return e.code,''
    except Exception: return 0,''
pages=[u.strip() for u in open('/tmp/urls.txt') if u.strip()]
# add blog listing + posts
st,bl=get(BASE+'/blog')
posts=sorted(set(re.findall(r'href="(https://www\.praxerasupplements\.com/blog/[a-z0-9\-]{6,})"',bl)))
targets=pages+[BASE+'/blog']+posts
print('crawling %d urls (%d pages, %d blog)'%(len(targets),len(pages),len(posts)+1))
res={}
def job(u):
    s,b=get(u); return u,s,b
with ThreadPoolExecutor(6) as ex:
    for u,s,b in ex.map(job,targets): res[u]=(s,b)
def vis(s):
    b=re.sub(r'<script.*?</script>','',s,flags=re.S|re.I); b=re.sub(r'<style.*?</style>','',b,flags=re.S|re.I)
    return re.sub(r'\s+',' ',H.unescape(re.sub(r'<[^>]+>',' ',b)))
rep=defaultdict(list)
for u,(s,b) in res.items():
    n=u.replace(BASE,'') or '/'
    if s!=200: rep['non200'].append((n,s)); continue
    v=vis(b)
    if re.search(r'(?i)da ?vinci',v): rep['davinci_visible'].append((n,len(re.findall(r'(?i)da ?vinci',v))))
    dl=set(re.findall(r'href="(https?://[^"]*davinci[^"]*)"',b))
    if dl: rep['davinci_links'].append((n,len(dl)))
    if 'navMenuLeft' not in b: rep['no_nav'].append((n,''))
    if re.findall(r'<a\b[^>]*href\s*=\s*""',b): rep['empty_href'].append((n,len(re.findall(r'<a\b[^>]*href\s*=\s*""',b))))
    h=re.findall(r'href="(/[^"#][^"]*)"',b)
    for x in set(h):
        if 'pl-demo' in x: rep['pl_demo'].append((n,x))
    t=re.search(r'<title>(.*?)</title>',b,re.S)
    if not t or not t.group(1).strip(): rep['no_title'].append((n,''))
    if re.search(r'(?i)\[[A-Z_]{3,}\]|coming soon|lorem ipsum',v): rep['placeholder'].append((n,''))
    if re.search(r'(?i)custom formulation',v): rep['custom_form'].append((n,''))
    if re.search(r'(?i)we manufacture|manufactured in our|our facility',v): rep['mfg_claim'].append((n,''))
json.dump({k:v for k,v in rep.items()},open('/tmp/fullqa.json','w'))
print()
order=['non200','davinci_visible','davinci_links','no_nav','empty_href','pl_demo','no_title','placeholder','custom_form','mfg_claim']
for k in order:
    v=rep.get(k,[])
    print('%-18s %3d'%(k,len(v)))
    for x in v[:6]: print('      ',x)
    if len(v)>6: print('       ... and %d more'%(len(v)-6))
