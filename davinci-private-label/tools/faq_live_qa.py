import sys, json, re, time, urllib.request
sys.path.insert(0,'/tmp')
from hs import call
faqs=json.load(open('/home/user/Claude/davinci-private-label/content/praxera_faqs.json'))
r=call('GET','/cms/v3/blogs/posts',q={'limit':100,'contentGroupId':'220598739286'})
pub=[p for p in r['results'] if p.get('state')=='PUBLISHED']
def get(u):
    for i in range(5):
        try:
            rq=urllib.request.Request(u+('&' if '?' in u else '?')+'cb=%d'%(time.time()*1000),
                                      headers={'User-Agent':'QBS-QA'})
            return urllib.request.urlopen(rq,timeout=45).read().decode('utf8','ignore')
        except Exception: time.sleep(4)
    return ''
ph=[]; missing=[]; ok=0; fail=[]
for p in pub:
    f=call('GET','/content/api/v2/blog-posts/%s'%p['id'])
    h=get(f['url'])
    if not h: fail.append(f.get('slug')); continue
    if 'Question goes here' in h: ph.append(f.get('slug'))
    if p['id'] in faqs:
        first=faqs[p['id']][0][0]
        probe=re.sub(r'[^a-z0-9 ]','',first.lower())[:45]
        flat=re.sub(r'[^a-z0-9 ]','',re.sub('<[^>]+>',' ',h).lower())
        flat=re.sub(r'\s+',' ',flat)
        if probe.strip() not in flat: missing.append((f.get('slug'),first[:60]))
        else: ok+=1
print('published checked:', len(pub)-len(fail), '| fetch failures:', len(fail), fail)
print('pages still showing "Question goes here":', len(ph), ph[:10])
print('new FAQs confirmed live: %d / %d'%(ok,len([p for p in pub if p["id"] in faqs])))
print('new FAQs NOT yet visible:', len(missing))
for m in missing[:12]: print('   ',m)
