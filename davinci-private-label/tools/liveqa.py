import sys, json, re, time, urllib.request, ssl
sys.path.insert(0,'/tmp')
from hs import call
D='/home/user/Claude/davinci-private-label/backups/hero-faq-restore'
r=call('GET','/cms/v3/blogs/posts',q={'limit':100,'contentGroupId':'220598739286'})
posts=[p for p in r['results'] if p.get('state')=='PUBLISHED']
meta={}
for p in posts:
    f=call('GET','/content/api/v2/blog-posts/%s'%p['id'])
    w=f.get('widgets') or {}
    hb=((w.get('hero') or {}).get('body') or {})
    fb=((w.get('faq') or {}).get('body') or {})
    meta[p['id']]={'url':f.get('url'),'slug':f.get('slug'),'title':f.get('html_title') or f.get('name'),
        'hero_h1':re.sub('<[^>]+>','',hb.get('headline','')).strip(),
        'faq_n':len(fb.get('items') or []), 'has_faq':'faq' in w}
def get(u):
    for i in range(4):
        try:
            rq=urllib.request.Request(u+('&' if '?' in u else '?')+'cb=%d'%time.time(),headers={'User-Agent':'QBS-QA'})
            return urllib.request.urlopen(rq,timeout=45).read().decode('utf8','ignore')
        except Exception as e:
            time.sleep(3)
    return ''
res=[]
for pid,m in meta.items():
    h=get(m['url'])
    if not h: res.append((pid,m['slug'],'FETCH-FAIL',None,None,None)); continue
    h1s=re.findall(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    h1t=[re.sub('<[^>]+>','',x).strip() for x in h1s]
    fallback='Your brand. Our formulations.' in h
    ph=h.count('Question goes here')
    ok_h1 = (not fallback) and any(m['hero_h1'].lower() in t.lower() or t.lower() in m['hero_h1'].lower() for t in h1t if t)
    res.append((pid,m['slug'],'OK' if ok_h1 else 'BAD-H1', h1t[:1], 'fallback' if fallback else '', 'placeholderFAQ=%d storedFAQ=%d'%(ph,m['faq_n'])))
json.dump(res,open(D+'/live-qa.json','w'),indent=1)
bad=[x for x in res if x[2]!='OK']
print('checked %d published posts'%len(res))
print('BAD:',len(bad))
for b in bad: print('  ',b)
phbad=[x for x in res if x[5] and 'placeholderFAQ=0' not in x[5]]
print('\nposts still showing placeholder FAQ:',len(phbad))
for x in phbad[:40]: print('  ',x[1],x[5])
