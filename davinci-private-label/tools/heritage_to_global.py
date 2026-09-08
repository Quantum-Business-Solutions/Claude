import sys, json, os, copy
sys.path.insert(0,'/tmp')
from hs import call
D='/home/user/Claude/davinci-private-label/backups/heritage-to-global'
GLOBAL_ID=218944099156
pages={(p.get('slug') or '(home)'):p for p in json.load(open('/tmp/prax_pages.json'))}

def convert(slug, dry=True):
    p=pages[slug]; pid=p['id']
    full=call('GET','/cms/v3/pages/site-pages/%s'%pid)
    before=copy.deepcopy(full.get('layoutSections') or {})
    ls=copy.deepcopy(before)
    swapped=[]; removed=[]
    # pass 1: the module holding the BODY becomes the global pointer
    def walk(n):
        if isinstance(n,dict):
            if n.get('type')=='module':
                pr=n.get('params') or {}
                c=json.dumps(pr)
                if 'most trusted dietary supplement' in c:
                    n['params']={'css_class':pr.get('css_class','dnd-module'),'module_id':GLOBAL_ID}
                    swapped.append(n.get('name'))
            for v in n.values(): walk(v)
        elif isinstance(n,list):
            for v in n: walk(v)
    walk(ls)
    # pass 2: a heading-only duplicate (Section Header carrying the same eyebrow/headline) is now redundant
    def walk2(n):
        if isinstance(n,dict):
            if n.get('type')=='module':
                pr=n.get('params') or {}
                c=json.dumps(pr)
                if ('50+ YEARS' in c or 'Developed by us' in c) and 'most trusted dietary supplement' not in c \
                   and pr.get('module_id')!=GLOBAL_ID:
                    removed.append(n.get('name'))
            for v in n.values(): walk2(v)
        elif isinstance(n,list):
            for v in n: walk2(v)
    walk2(ls)
    if dry: return {'slug':slug,'state':full.get('state'),'swap':swapped,'redundant_heading':removed}
    os.makedirs(D,exist_ok=True)
    json.dump({'slug':slug,'id':pid,'state':full.get('state'),'layoutSections':before},
              open(os.path.join(D,slug.replace('/','_')+'.before.json'),'w'),indent=1)
    call('PATCH','/cms/v3/pages/site-pages/%s'%pid,{'layoutSections':ls})
    act='LEFT DRAFT'
    if (full.get('state') or '').startswith('PUBLISHED'):
        call('POST','/cms/v3/pages/site-pages/%s/draft/push-live'%pid,{}); act='pushed live'
    after=call('GET','/cms/v3/pages/site-pages/%s'%pid)
    blob=json.dumps(after.get('layoutSections') or {})
    return {'slug':slug,'swap':swapped,'redundant_heading':removed,'action':act,
            'state':after.get('state'),
            'inline_text_left': 'most trusted dietary supplement' in blob,
            'points_to_global': str(GLOBAL_ID) in blob}
