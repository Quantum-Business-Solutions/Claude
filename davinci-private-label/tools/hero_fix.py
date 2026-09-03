import sys, json, time
sys.path.insert(0,'/tmp')
from hs import call
D='/home/user/Claude/davinci-private-label/backups/hero-faq-restore'
before=json.load(open(D+'/before.json'))
ids=sys.argv[1:]
FIX=('hero','faq','disclaimer')
log=[]
for pid in ids:
    meta=before[pid]
    full=call('GET','/content/api/v2/blog-posts/%s'%pid)
    w=full.get('widgets') or {}
    cleared=[]
    for n in FIX:
        v=w.get(n)
        if isinstance(v,dict) and v.get('deleted_at'):
            v['deleted_at']=None
            cleared.append(n)
    if not cleared:
        log.append((pid,meta['slug'],'NOTHING-TO-DO')); continue
    call('PUT','/content/api/v2/blog-posts/%s'%pid, {'widgets': w})
    rb=call('GET','/content/api/v2/blog-posts/%s'%pid)
    rw=rb.get('widgets') or {}
    still=[n for n in FIX if isinstance(rw.get(n),dict) and rw[n].get('deleted_at')]
    pub=''
    if meta['state']=='PUBLISHED':
        call('POST','/content/api/v2/blog-posts/%s/publish-action'%pid, {'action':'schedule-publish'})
        pub='republished'
    else:
        pub='LEFT-DRAFT'
    st=call('GET','/content/api/v2/blog-posts/%s'%pid).get('state')
    log.append((pid,meta['slug'],'cleared=%s'%','.join(cleared),'still_flagged=%s'%(still or 'none'),pub,'state=%s(was %s)'%(st,meta['state'])))
for l in log: print(' | '.join(str(x) for x in l))
