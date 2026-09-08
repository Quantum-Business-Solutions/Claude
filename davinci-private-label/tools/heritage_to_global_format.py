import sys, json, os, copy, re, urllib.request, time
sys.path.insert(0,'/tmp')
from hs import call
D='/home/user/Claude/davinci-private-label/backups/heritage-to-global'
GLOBAL_ID=218944099156
pages={(p.get('slug') or '(home)'):p for p in json.load(open('/tmp/prax_pages.json'))}
def convert_format(slug, dry=True):
    p=pages[slug]; pid=p['id']
    full=call('GET','/cms/v3/pages/site-pages/%s'%pid)
    before=copy.deepcopy(full.get('layoutSections') or {}); ls=copy.deepcopy(before)
    swapped=[]; removed_rows=[]
    def is_header(n):
        pr=n.get('params') or {}; c=json.dumps(pr)
        return n.get('type')=='module' and ('50+ YEARS' in c or 'Developed by us' in c) and 'most trusted dietary supplement' not in c and pr.get('module_id')!=GLOBAL_ID
    def is_body(n):
        return n.get('type')=='module' and 'most trusted dietary supplement' in json.dumps(n.get('params') or {})
    def row_has(row,pred):
        found=[]
        def w(n):
            if isinstance(n,dict):
                if pred(n): found.append(n)
                for v in n.values(): w(v)
            elif isinstance(n,list):
                for v in n: w(v)
        w(row); return found
    def walk(n):
        if isinstance(n,dict):
            if isinstance(n.get('rows'),list):
                keep=[]
                for row in n['rows']:
                    hb=row_has(row,is_body); hh=row_has(row,is_header)
                    if hh and not hb:
                        removed_rows.append([m.get('name') for m in hh]); continue   # drop the duplicate-heading row
                    for m in hb:
                        m['params']={'css_class':(m.get('params') or {}).get('css_class','dnd-module'),'module_id':GLOBAL_ID}
                        swapped.append(m.get('name'))
                    keep.append(row)
                n['rows']=keep
            for v in n.values(): walk(v)
        elif isinstance(n,list):
            for v in n: walk(v)
    walk(ls)
    if dry: return {'slug':slug,'swap':swapped,'removed_header_rows':removed_rows}
    os.makedirs(D,exist_ok=True)
    json.dump({'slug':slug,'id':pid,'state':full.get('state'),'layoutSections':before},open(os.path.join(D,slug.replace('/','_')+'.before.json'),'w'),indent=1)
    call('PATCH','/cms/v3/pages/site-pages/%s'%pid,{'layoutSections':ls})
    act='LEFT DRAFT'
    if (full.get('state') or '').startswith('PUBLISHED'):
        call('POST','/cms/v3/pages/site-pages/%s/draft/push-live'%pid,{}); act='pushed live'
    after=call('GET','/cms/v3/pages/site-pages/%s'%pid); blob=json.dumps(after.get('layoutSections') or {})
    return {'slug':slug,'swap':swapped,'removed_header_rows':removed_rows,'action':act,'state':after.get('state'),
            'inline_text_left':'most trusted dietary supplement' in blob,'points_to_global':str(GLOBAL_ID) in blob,
            'header_dup_left': blob.count('50+ YEARS')}
if __name__=='__main__':
    import json as j
    print('DRY gummies:', j.dumps(convert_format('gummies',dry=True)))
    r=convert_format('gummies',dry=False); print('LIVE gummies:', j.dumps(r))
