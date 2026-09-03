import sys, json, os
sys.path.insert(0,'/tmp')
from hs import call
D='/home/user/Claude/davinci-private-label/backups/faq-authoring'
os.makedirs(D,exist_ok=True)
faqs=json.load(open('/home/user/Claude/davinci-private-label/content/praxera_faqs.json'))

TPL={'name':'faq','path':'/Private Label/Modules/PL - FAQ','type':'module'}
BODY={'answer_size':15,'css_class':'dnd-module','headline_size':32,'max_width':820,
 'open_first':False,'question_size':17,'section_eyebrow':'',
 'section_headline':'Frequently asked questions','section_id':'',
 'style':{'background_color':{'color':'#f7f7f6','opacity':100},
          'padding':{'padding_bottom':80,'padding_top':80}},
 'text_color':'dark'}

before={}
for pid in faqs:
    f=call('GET','/content/api/v2/blog-posts/%s'%pid)
    before[pid]={'slug':f.get('slug'),'state':f.get('state'),'publish_date':f.get('publish_date'),
                 'widgets':f.get('widgets')}
json.dump(before,open(D+'/before.json','w'),indent=1)
print('backed up',len(before),'posts')

log=[]
for pid,items in faqs.items():
    f=call('GET','/content/api/v2/blog-posts/%s'%pid)
    w=f.get('widgets') or {}
    st=f.get('state')
    body=dict(BODY); body['items']=[{'question':q,'answer':'<p>%s</p>'%a} for q,a in items]
    node=dict(TPL); node['body']=body
    w['faq']=node
    call('PUT','/content/api/v2/blog-posts/%s'%pid,{'widgets':w})
    rb=call('GET','/content/api/v2/blog-posts/%s'%pid)
    rw=rb.get('widgets') or {}
    n=len(((rw.get('faq') or {}).get('body') or {}).get('items') or [])
    pub='LEFT-DRAFT'
    if st=='PUBLISHED':
        call('POST','/content/api/v2/blog-posts/%s/publish-action'%pid,{'action':'schedule-publish'})
        pub='republished'
    fin=call('GET','/content/api/v2/blog-posts/%s'%pid)
    same_date = fin.get('publish_date')==before[pid]['publish_date']
    log.append((pid,before[pid]['slug'],'items=%d'%n,pub,'state=%s'%fin.get('state'),'date_kept=%s'%same_date))
json.dump(log,open(D+'/apply-log.json','w'),indent=1)
ok=sum(1 for l in log if l[2]=='items=3' and l[5]=='date_kept=True')
print('applied: %d/%d wrote 3 items with publish_date preserved'%(ok,len(log)))
for l in log:
    if l[2]!='items=3' or l[5]!='date_kept=True': print('  ISSUE',l)
print('states:',{s:sum(1 for l in log if l[4]==s) for s in set(l[4] for l in log)})
