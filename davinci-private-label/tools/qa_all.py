import sys,json,re,html as H,datetime
sys.path.insert(0,'/tmp')
from hs import call
prax=json.load(open('/tmp/prax.json'))
def plain(s):
    s=re.sub(r'<br\s*/?>',' ',s); s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',H.unescape(s)).strip()
S={}   # signal -> list of (page, detail)
def add(k,p,d=''): S.setdefault(k,[]).append((p,d))
now=datetime.datetime.utcnow(); active=[]
for p in prax:
    slug=p['slug'] or '(home)'
    d=call('GET','/cms/v3/pages/site-pages/%s/draft'%p['id'])
    raw=json.dumps(d)
    txt=plain(' '.join(re.findall(r'"([^"]{15,})"',raw)))
    ht=d.get('htmlTitle') or ''; md=d.get('metaDescription') or ''
    u=d.get('updatedAt','')[:19]
    try:
        if (now-datetime.datetime.strptime(u,'%Y-%m-%dT%H:%M:%S')).total_seconds()/60 < 20: active.append(slug)
    except: pass
    # --- 2 Sep call items ---
    if re.search(r'(?i)custom formulation',txt): add('customFormulation',slug,str(len(re.findall(r'(?i)custom formulation',txt))))
    if re.search(r'(?i)dropship',txt): add('dropship',slug,str(len(re.findall(r'(?i)dropship',txt))))
    for m in re.finditer(r'(?i)we manufacture|we can manufacture|manufactured in our|we have certified manufacturing|trusted dietary supplement manufacturers|we are on the FDA|manufacturing-side|that same manufacturing standard|access to manufacturing infrastructure',txt): add('mfgFirstPerson',slug,m.group(0)[:38])
    if 'pl-demo-pillar' in raw: add('brokenAndMore',slug)
    if re.search(r'>None<',raw): add('noneBlock',slug)
    if re.search(r'\[[A-Z_]{3,}\]',txt): add('bracketPlaceholder',slug)
    if re.search(r'(?i)BRAND_TBD',raw): add('brandTBD',slug)
    if re.search(r'(?i)coming soon|placeholder for',txt): add('placeholderCopy',slug,plain(re.search(r'(?i)[^.]{0,60}(coming soon|placeholder for)[^.]{0,40}',txt).group(0))[:70])
    if re.search(r'(?i)talk to a designer',txt): add('talkToDesigner',slug)
    if re.search(r'(?i)work with our design team',txt): add('ourDesignTeam',slug)
    if re.search(r'(?i)\bamazon\b',txt): add('amazonMention',slug,str(len(re.findall(r'(?i)\bamazon\b',txt))))
    if re.search(r'(?i)\bda ?vinci\b',txt): add('davinciVisibleText',slug)
    for a in re.findall(r'"alt":\s*"([^"]*)"',raw):
        if re.search(r'(?i)da ?vinci',a): add('davinciAlt',slug,a[:40])
        if re.search(r'(?i)prexera',a): add('prexeraAlt',slug,a[:40])
    if re.search(r'(?i)davincilabs\.com',raw): add('davinciImageHost',slug,str(len(re.findall(r'(?i)davincilabs\.com',raw))))
    if re.search(r'(?i)foodscience',txt): add('foodscienceMention',slug,str(len(re.findall(r'(?i)foodscience',txt))))
    if '®' in txt or '™' in txt: add('trademarkSymbol',slug,str(txt.count('®')+txt.count('™')))
    if re.search(r'(?i)melinda',txt): add('melindaTestimonial',slug)
    if re.search(r'(?i)elmadjian',txt): add('elmadjianAttrib',slug)
    # --- SEO ---
    if len(ht)>60: add('titleTooLong',slug,str(len(ht)))
    if ht.lower().count('private label')>1: add('titleRepeatsPL',slug)
    if not md: add('metaMissing',slug)
    if 'QBS-SCHEMA:START' in (d.get('headHtml') or ''): add('schemaPresent',slug)
    if re.search(r'href="#"',raw): add('deadHashLink',slug)
    del d,raw,txt
json.dump({k:v for k,v in S.items()},open('/tmp/qa.json','w'))
print('ACTIVE EDITS in last 20 min:',len(active),sorted(active)[:10])
print()
order=['customFormulation','mfgFirstPerson','dropship','placeholderCopy','davinciVisibleText','davinciAlt','prexeraAlt',
       'talkToDesigner','ourDesignTeam','amazonMention','elmadjianAttrib','melindaTestimonial',
       'brokenAndMore','noneBlock','bracketPlaceholder','brandTBD','deadHashLink',
       'davinciImageHost','foodscienceMention','trademarkSymbol','titleTooLong','titleRepeatsPL','metaMissing','schemaPresent']
for k in order:
    v=S.get(k,[]); pages=sorted(set(x[0] for x in v))
    print('%-22s %4d hits / %2d pages'%(k,len(v),len(pages)))
    if 0<len(pages)<=8: print('        ',', '.join(pages))
