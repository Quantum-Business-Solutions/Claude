import sys, json, time
sys.path.insert(0,'/tmp')
from hs import call
r=call('GET','/cms/v3/blogs/posts',q={'limit':100,'contentGroupId':'220598739286','property':'id,slug,name,state'})
posts=r.get('results',[])
out=[]
for p in posts:
    pid=p['id']
    full=call('GET','/content/api/v2/blog-posts/%s'%pid)
    w=full.get('widgets') or {}
    bad={}
    for wname,wv in w.items():
        if isinstance(wv,dict) and 'deleted_at' in wv and wv.get('deleted_at'):
            bad[wname]=wv.get('deleted_at')
    out.append({'id':pid,'slug':p.get('slug'),'name':p.get('name'),'state':p.get('state'),
                'bad':bad,'widget_names':sorted(w.keys())})
json.dump(out,open('/tmp/hero_scan.json','w'),indent=1)
nb=[o for o in out if o['bad']]
print('total posts',len(out),'posts with deleted_at widgets',len(nb))
from collections import Counter
c=Counter()
for o in nb:
    for k in o['bad']: c[k]+=1
print('widget breakdown:',dict(c))
for o in nb[:50]: print(' ',o['id'],o['state'],o['slug'],list(o['bad'].keys()))
