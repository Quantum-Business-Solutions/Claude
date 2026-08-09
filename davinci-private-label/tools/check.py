import json,re,urllib.request,os,difflib,html as _html,sys
T=os.environ['TOKEN']; H={"Authorization":"Bearer "+T}
BK='/tmp/claude-0/-home-user-Claude/0f427e52-eb7f-5b23-8772-a7e122ea7371/scratchpad/backup_v1/'
def get(p): return json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://api.hubapi.com/cms/v3/pages/site-pages/{p}",headers=H)))
def render(pid):
    p=json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://api.hubapi.com/content/api/v2/pages/{pid}",headers=H)))
    return urllib.request.urlopen(urllib.request.Request(
        f"https://info.davincilabs.com/{p['slug']}?hs_preview={p['preview_key']}-{pid}",
        headers={"User-Agent":"Mozilla/5.0"})).read().decode('utf-8','replace')
def clean(h):
    h=re.sub(r'(?is)<(script|style)\b.*?</\1>',' ',h); h=re.sub(r'(?s)<!--.*?-->',' ',h)
    return re.sub(r'\s+',' ',_html.unescape(re.sub(r'<[^>]+>',' ',h))).strip()
def body_text(h):
    i=h.find('container-fluid'); h=h[h.find('>',i)+1:] if i>0 else h
    cut=h.find('global_footer')
    if cut>0: cut=h.rfind('<',0,cut)      # back up to the tag start, or we truncate mid-tag
    return clean(h[:cut] if cut>0 else h)
def v1_widgets(v1id):
    v1=get(v1id); ws=(v1.get('widgetContainers') or {}).get('main_content',{}).get('widgets',[])
    if not ws:
        import os
        for cand in (f'../promote/{v1id}.PRE.json',
                     f'/home/user/Claude/davinci-private-label/snapshots/v1-pre-promotion/{v1id}.json',
                     f'../backup_v1_2026-08-07/{v1id}.json', f'{v1id}.json', BK+f'{v1id}.json'):
            if os.path.exists(cand):
                snap=json.load(open(cand))
                ws=(snap.get('widgetContainers') or {}).get('main_content',{}).get('widgets',[])
                if ws: break
    return ws


def v1_h1(v1id):
    """How many <h1> V1 had. The privacy and terms pages have none, and adding
    one would be a change, not a fix -- so the rule is 'match V1', except where
    V1 had more than one, which we deliberately collapse to a single heading."""
    h=' '.join((w.get('body',{}).get('html') or w.get('body',{}).get('value') or '')
               for w in v1_widgets(v1id))
    return len(re.findall(r'<h1[ >]', h))


def v1_text(v1id):
    v1=get(v1id); ws=(v1.get('widgetContainers') or {}).get('main_content',{}).get('widgets',[])
    if not ws:
        # page already promoted: its record no longer holds the rich text
        import os
        for cand in (f'../promote/{v1id}.PRE.json', f'../backup_v1_2026-08-07/{v1id}.json',
                     f'{v1id}.json', BK+f'{v1id}.json'):
            if os.path.exists(cand):
                snap=json.load(open(cand))
                ws=(snap.get('widgetContainers') or {}).get('main_content',{}).get('widgets',[])
                if ws: break
        if not ws: raise RuntimeError(f'no V1 body available for {v1id}')
    # A global widget's body is empty by design, so its text comes from the June
    # backup. Match on module_id, not list position: design-services gained a
    # global after the backup was taken, and by position it then counted its
    # heritage twice and lost its FDA disclaimer. Widget ids are not usable --
    # re-inserting a global mints a new one -- so position is the last resort.
    june=[]
    try: june=json.load(open(BK+f'{v1id}.json'))['widgetContainers']['main_content']['widgets']
    except Exception: pass
    by_mod={}
    for jw in june:
        t=(jw.get('body') or {}).get('html') or (jw.get('body') or {}).get('content') or ''
        if jw.get('module_id') and t.strip(): by_mod.setdefault(jw['module_id'], t)
    parts=[]
    for i,w in enumerate(ws):
        b=w.get('body') or {}; t=b.get('html') or b.get('content') or ''
        if not t.strip():
            t=by_mod.get(w.get('module_id')) or ''
            if not t.strip() and i < len(june):
                jb=june[i].get('body') or {}
                t=jb.get('html') or jb.get('content') or ''
        parts.append(t)
    return clean(' '.join(parts))
def module_count(v3id):
    """How many modules the page actually holds. The section count was hard-coded
    to 14 for the category family; on any other page that constant is either a
    false failure or, worse, never exercised."""
    d = get(v3id)
    c = (d.get('layoutSections') or {}).get('main_content', {})
    return sum(len(sr) for row in c.get('rows', []) for ck in row for sr in row[ck]['rows'])


def check(v1id,v3id,label):
    h=render(v3id); a=v1_text(v1id); b=body_text(h)
    sm=difflib.SequenceMatcher(None,a.split(),b.split()); lost=[]; gained=[]
    for op,i1,i2,j1,j2 in sm.get_opcodes():
        if op in ('delete','replace'): lost+=a.split()[i1:i2]
        if op in ('insert','replace'): gained+=b.split()[j1:j2]
    bad=[w for w in lost if w.strip() not in {'+','−','None',''}]
    err=len(re.findall(r'(?i)hubl error|jinjava',h)); sec=len(re.findall(r'dnd-section',h))
    body=h[h.find('container-fluid'):]
    cut=body.find('global_footer')
    if cut>0: cut=body.rfind('<',0,cut)
    body=body[:cut] if cut>0 else body
    h1=len(re.findall(r'<h1[ >]',body))                 # exactly one, or the page has no title
    junk=len(re.findall(r'</svg>|</div>',
              ' '.join(re.findall(r'<div class="pl-cg__content">(.*?)</div>',body,re.S))))
    inv=[w for w in gained if w.strip() not in {'+','−',''}]
    want = module_count(v3id)
    want_h1 = 1 if v1_h1(v1id) >= 1 else 0
    ok = (not bad) and not inv and err==0 and sec==want and h1==want_h1 and junk==0
    print("  %-26s %-4s  sections:%d/%-3d err:%d  h1:%d/%d  junk:%d  lost:%d  invented:%d %s" % (
        label,"PASS" if ok else "FAIL",sec,want,err,h1,want_h1,junk,len(bad),len(inv),
        (bad[:6] or inv[:6]) if (bad or inv) else ''))
    return ok
if __name__=='__main__':
    sys.exit(0 if check(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else sys.argv[1]) else 1)
