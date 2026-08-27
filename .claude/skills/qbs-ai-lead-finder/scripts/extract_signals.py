#!/usr/bin/env python3
"""
Signal extraction. Eight date sources tried in descending trust; first match wins.

Carries every fix from the UBEO run: fuzzy quantifiers, 10/31 year-pinning,
numeric month capture, month-to-month retention, one-cycle projection cap,
lease-context requirement on loose rules, email thread-stripping, negation
guards, and a final check that every signal contains its own basis phrase.

  python3 extract_signals.py <pool.json> <out.json> <field1,field2> <type>

Then run:  python3 qa_gates.py extract --signals <out.json> --pool <pool.json>
"""
import json,re,datetime,collections,sys
today=datetime.date(2026,8,26)
WINDOW_BACK=datetime.date(2025,8,26)   # dates this recent are still in play
POOL=sys.argv[1]; OUT=sys.argv[2]; BODYP=sys.argv[3].split(","); TYP=sys.argv[4]
pool=json.load(open(POOL))
QUOTED=re.compile(r'(?is)(?:^|\n)\s*(?:On .{0,80}?wrote:|-{2,}\s*Original Message|From:\s.{0,60}?Sent:|_{5,}|>{1,}\s).*$')
SIGBLOCK=re.compile(r'(?is)(?:\n|^)\s*(?:Sincerely|Regards|Best regards|Thanks?,|Thank you,)[\s,]*\n.*$')
def strip_thread(t):
    """emails carry quoted reply chains + signatures - a lease word 40 lines away
    from a date is not evidence. Keep only the top (newest) message."""
    t=QUOTED.sub(' ',t or '')
    t=SIGBLOCK.sub(' ',t)
    return t

def sentences(t):
    return re.split(r'(?<=[.!?])\s+|\n{2,}|\|\|',t or '')

def clean(t): return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',t or '').replace('&nbsp;',' ').replace('&amp;','&').replace('&#x27;',"'")).strip()
def strip_legacy(b): return re.sub(r'SalesChainID:\s*\d+|Annual Revenue:\s*[\d.]+|Federal ID Number:\s*\d+|SICCode:\s*\d+|Toll Free:\s*\([^)]*\)\s*[\d-]*','',b).strip()
MON={m.lower():i+1 for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
for a,i in list(MON.items()): MON[a[:3]]=i
MON['sept']=9; MON['tues']=None
def monthof(tok):
    t=(tok or '').lower().strip('.')
    if not t: return None
    if t in MON and MON[t]: return MON[t]
    if len(t)>=3 and t[:3] in MON and MON[t[:3]]: return MON[t[:3]]   # SEPT, JANU, DECEM...
    return None
W={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eighteen':18,'twelve':12,'a':1,'another':1,
   'couple':2,'couple of':2,'few':3,'several':4,'half':0.5}
def n2(s):
    if s is None: return None
    s=str(s).lower().strip()
    return W.get(s) if s in W else (float(s) if re.match(r'^\d+(\.\d+)?$',s) else None)
def mk(y,m=1):
    try:
        y=int(y); y=y+2000 if y<100 else y
        if not (2000<=y<=2040): return None
        return datetime.date(y,int(m) if 1<=int(m)<=12 else 1,1)
    except: return None
def addy(base,y):
    try: return base.replace(year=base.year+int(y))
    except: return base+datetime.timedelta(days=int(365*float(y)))
ABS=re.compile(r"(?:lease|contract|agreement|deal)[^.]{0,60}?(?:expires?|expiring|expire|ends?|ending|is up|up|due|thru|through|good (?:until|thru)|runs? (?:to|until|through)|does not end until)\s*(?:in|on|around|end of|until|til|of)?\s*([A-Za-z]+)?\s*(?:of\s+)?['\u2019]?(\d{1,2})?[/-]?(\d{1,2})?[/-]?['\u2019]?(\d{2,4})['\u2019]?",re.I)
REM=re.compile(r'\b(?:a\s+)?(\d+(?:\.\d+)?|one|two|three|four|five|six|eighteen|twelve|couple of|couple|few|several)\s*(?:more\s+)?(yrs?|years?|months?|mos?)\s*(?:left|remaining|to go|out)\b',re.I)
FUZZY=re.compile(r'\b(?:a\s+)?(couple|few|several)\s+(?:more\s+)?(?:of\s+)?(yrs?|years?|months?|mos?)\b[^.]{0,25}?(?:left|remaining|to go|on (?:the|their) (?:lease|contract))',re.I)
HALF=re.compile(r'\b(?:a\s+)?year\s+and\s+a\s+half\b|\ba year or two\b',re.I)
ONLEASE=re.compile(r'\b(\d+(?:\.\d+)?|one|two|three|four|five|six)\s*(yrs?|years?|months?|mos?)\s+(?:on|out on|left on)\s+(?:the\s+|their\s+)?(?:lease|contract)\b',re.I)
INTO=re.compile(r'\b(\d+(?:\.\d+)?|one|two|three|four|five)\s*(?:yrs?|years?)?\s+into\s+(?:a|their|the)?\s*(\d+)\s*(?:yrs?|years?)\b',re.I)
TERM_START=re.compile(r'\b(\d+|one|two|three|four|five|six|seven)[\s-]*(?:yr|yrs|year|years)\b[^.]{0,40}?\b(?:lease|contract|agreement|deal)\b[^.]{0,35}?\b(?:([A-Za-z]+)|(\d{1,2}))?[\s/\-]*(20\d{2})\b',re.I)
SIGNED_YEAR=re.compile(r'\b(?:signed|started|began|new)\b[^.]{0,50}?\b(?:lease|contract|agreement|deal)\b[^.]{0,45}?\b(?:in\s+)?(?:([A-Za-z]+)|(\d{1,2}))?[\s/\-]*(20\d{2})\b(?:[^.]{0,30}?(?:for\s+)?(\d+|one|two|three|four|five|six|seven)\s*(?:yr|yrs|year|years))?',re.I)
RENEWED_FOR=re.compile(r'\b(?:renewed|re-?signed|signed|extended|locked in|good)\b[^.]{0,45}?\bfor\s+(?:another\s+)?(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|a)\s*(yrs?|years?|months?|mos?)\b',re.I)
ANOTHER=re.compile(r'\bfor\s+another\s+(\d+(?:\.\d+)?|one|two|three|four|five|six|seven)?\s*(yrs?|years?|months?|mos?)\b',re.I)
AUTOREN2=re.compile(r'\bauto[- ]?renew(?:ed|s|al)?\b|\bautomatically renewed\b|\brolled over\b',re.I)
M2M=re.compile(r'\bmonth[- ]to[- ]month\b|\bmonth 2 month\b|\bm2m\b',re.I)
M2M_NEG=re.compile(r"\b(?:not|isn'?t|aren'?t|no longer|never)\b[^.]{0,25}?month[- ]to[- ]month",re.I)
def is_m2m(b): return bool(M2M.search(b)) and not M2M_NEG.search(b)
SIGNED=re.compile(r'\b(?:just|recently|newly)\s+(?:signed|renewed|re-?signed)|\bsigned\s+(?:a\s+)?new\b|\brenewed\s+(?:their|our|the)\b',re.I)
SIGTERM=re.compile(r'\b(\d+|three|four|five|six|seven)\s*(?:yr|yrs|year|years)\b',re.I)
AGO=re.compile(r'\b(?:last year|a year ago|(\d+)\s*(?:yrs?|years?)\s+ago|back in (\d{4}))\b',re.I)
UBEO=re.compile(r'\blease\s+with\s+us\b|\bwith us that expires\b|\bwe sold\b|\bsold off lease\b|\bthrough us\b|\bcurrent customer\b|\bwith us\b|\bfrom us\b',re.I)
DNC=re.compile(r'\bXDNC\b|\bDO NOT CALL\b|\bstop calling\b',re.I)
OWN=re.compile(r'\bown (?:their|our|the|them|it)\b|\bpurchased (?:their|the)\b|\bowns? (?:their|the)\b',re.I)
OEM=re.compile(r'\b(Ricoh|Xerox|Canon|Konica(?:\s+Minolta)?|Minolta|Sharp|Toshiba|Kyocera|Lanier|Savin|Muratec|Lexmark|Brother|Epson)\b',re.I)
AUTOREN=re.compile(r'\bauto(?:matic)?[- ]?renew\w*|\bevergreen\b',re.I)
APOS=re.compile(r"(?:lease|contract|agreement|deal)[^.]{0,40}?['\u2019](\d{2})\b|(?:lease|contract|agreement|deal)[^.]{0,40}?\b(\d{2})['\u2019]",re.I)
YEARONLY=re.compile(r'\b(?:lease|contract|agreement|deal)\b[^.]{0,45}?\b(20\d{2})\b(?!\s*[/-])',re.I)
TERMLEN=re.compile(r'\b(\d+|three|four|five|six|seven)[\s-]*(?:yr|yrs|year|years)\b[^.]{0,45}?\b(?:lease|contract|agreement|deal)\b|\b(?:lease|contract|agreement|deal)\b[^.]{0,25}?\b(\d+|three|four|five|six|seven)[\s-]*(?:yr|yrs|year|years)\b',re.I)
_W2={'three':3,'four':4,'five':5,'six':6,'seven':7}
def termlen(b):
    m=TERMLEN.search(b)
    if not m: return None
    v=m.group(1) or m.group(2)
    if not v: return None
    n=_W2.get(str(v).lower()) or (int(v) if str(v).isdigit() else None)
    return n if n and 2<=n<=7 else None
LEASECTX=re.compile(r'\b(lease|leases|leasing|leased|contract|contracts|agreement|deal|term)\b',re.I)
def near_lease(b,m,w=100):
    """loose quantity rules must sit near a lease/contract word to count"""
    i=m.start(); return bool(LEASECTX.search(b[max(0,i-w):m.end()+w]))

def derive(b,base):
    m=ABS.search(b)
    if m:
        mo,d1,d2,y=m.groups()
        monthnum=monthof(mo) or (int(d1) if d1 and d1.isdigit() and 1<=int(d1)<=12 else None)
        e=mk(y,monthnum or 1)
        if e:
            if monthnum is None:
                # only a YEAR was stated - Jan 1 is an artifact of defaulting, not data.
                # pin to 10/31 of that year so it neither sorts as expired nor claims false precision.
                e=datetime.date(e.year,10,31)
                return e,m.group(0),"stated year only (pinned 10/31)"
            return e,m.group(0),"stated date"
    m=RENEWED_FOR.search(b) or ANOTHER.search(b)
    if m:
        g=m.groups()
        n=n2(g[0]) if g[0] else 1
        u=(g[1] or 'y').lower()
        if n:
            e=base+datetime.timedelta(days=int(30*n)) if u.startswith('mo') else addy(base,n)
            return e,m.group(0),"computed from renewal term"
    m=APOS.search(b)
    if m:
        yy=m.group(1) or m.group(2)
        e=mk(yy)
        if e and 2024<=e.year<=2035:
            return datetime.date(e.year,10,31),m.group(0),"stated year only (pinned 10/31)"
    for rx,lbl in ((REM,"remaining term"),(ONLEASE,"remaining term"),(FUZZY,"remaining term (approx)")):
        m=rx.search(b)
        if m and ("approx" in lbl) and not near_lease(b,m): continue
        if m:
            n=n2(m.group(1))
            if n is not None:
                u=(m.group(2) or 'y').lower()
                e=base+datetime.timedelta(days=int(30*n)) if u.startswith('mo') else addy(base,n)
                return e,m.group(0),"computed from %s"%lbl
    m=HALF.search(b)
    if m and near_lease(b,m): return addy(base,1.5),m.group(0),"computed from remaining term (approx)"
    m=INTO.search(b)
    if m:
        el,tot=n2(m.group(1)),n2(m.group(2))
        if el is not None and tot and tot>el: return addy(base,tot-el),m.group(0),"computed from remaining term"
    m=SIGNED_YEAR.search(b)
    if m:
        mo,mnum,yr,term=m.groups()
        mk_month=monthof(mo) or (int(mnum) if mnum and 1<=int(mnum)<=12 else None)
        start=mk(yr,mk_month or 1)
        n=n2(term)
        if start and n:
            e=addy(start,n)
            if mk_month is None: e=datetime.date(e.year,10,31)   # month never known -> pin
            return e,m.group(0),"computed from signed-year + term"
    m=TERM_START.search(b)
    if m:
        n=n2(m.group(1)); mo,mnum,yr=m.group(2),m.group(3),m.group(4)
        mk_month=monthof(mo) or (int(mnum) if mnum and 1<=int(mnum)<=12 else None)
        start=mk(yr,mk_month or 1)
        if start and n:
            e=addy(start,n)
            if mk_month is None: e=datetime.date(e.year,10,31)   # month never known -> pin
            return e,m.group(0),"computed from term + start year"
    if SIGNED.search(b):
        m=SIGTERM.search(b); n=n2(m.group(1)) if m else None
        if n and 2<=n<=7:
            start=base; a=AGO.search(b)
            if a:
                if a.group(1): start=addy(base,-float(a.group(1)))
                elif a.group(2):
                    s2=mk(a.group(2)); start=s2 or base
                else: start=addy(base,-1)
            return addy(start,n),"%s term, signed %s"%(m.group(0),start.strftime('%m/%Y')),"computed from just-signed"
    return None,None,None
out=[];stale=0
for rid,r in pool.items():
    p=r["properties"]
    parts=[clean(p.get(k)) for k in BODYP]
    if TYP=="meeting":
        seen_=set(); merged=[]
        for t in parts:
            if t and t[:60] not in seen_: seen_.add(t[:60]); merged.append(t)
        parts=[" || ".join(merged),""]
    body=parts[0] if parts else ""
    extra=parts[1] if len(parts)>1 else ""
    b=strip_legacy(body if extra and extra[:60] in body else (body+" || "+extra if body else extra))
    if len(b)<25: continue
    ts=(p.get("hs_timestamp") or "")[:10]
    try: base=datetime.date(*map(int,ts.split("-")))
    except: continue
    if TYP=="email":
        b=strip_thread(b)
        # require the lease word and the date inside ONE sentence
        hit=None
        for sent in sentences(b):
            if len(sent)<20: continue
            if not re.search(r'\b(lease|leases|leasing|leased|contract|contracts|agreement)\b',sent,re.I): continue
            r_=derive(sent,base)
            if r_[0]: hit=r_; break
        e,basis,src=hit if hit else (None,None,None)
    else:
        e,basis,src=derive(b,base)
    if not e and is_m2m(b):
        # no lease to wait for - winnable immediately. date = today so it sorts to the top.
        e=today; basis=M2M.search(b).group(0); src="month-to-month (no lease term)"
    if not e: continue
    proj=""
    if e<WINDOW_BACK:
        # RULE A: year-only date inside the current year -> pin to 10/31 of that year
        if e.year==today.year and YEARONLY.search(b):
            e=datetime.date(today.year,10,31); proj=" [year-only date pinned to 10/31]"
        else:
            # RULE B: roll forward ONE term length only
            L=termlen(b)
            rolled=None
            if L:
                try: rolled=e.replace(year=e.year+L)
                except: rolled=e+datetime.timedelta(days=365*L)
            if rolled and rolled>=today:
                if e.month==1 and e.day==1: rolled=datetime.date(rolled.year,10,31)  # source month unknown
                e=rolled; proj=" [PROJECTED: prior %dyr term ended %s, one renewal assumed]"%(L,basis and '')
                src="projected next cycle (1 renewal)"
            else:
                stale+=1; continue
    flags=[]
    if is_m2m(b): flags.append("MONTH_TO_MONTH_NO_LEASE")
    if AUTOREN2.search(b): flags.append("AUTO_RENEW_NOTICE_WINDOW")
    if (e-today).days<0: flags.append("IN_PLAY_VERIFY")
    if DNC.search(b): flags.append("DNC")
    if UBEO.search(b): flags.append("UBEO_INCUMBENT")
    if OWN.search(b) and not re.search(r'\blease',b,re.I): flags.append("OWNS_EQUIPMENT")
    if AUTOREN.search(b): flags.append("AUTO_RENEW")
    if basis and basis.split(" term,")[0].lower() not in b.lower():
        continue   # evidence cannot be centred on a phrase we can't find - do not ship it
    out.append({"engagement_id":rid,"engagement_type":TYP,"ts":ts,"end":e.isoformat(),
                "basis":basis,"src":src,"flags":flags,
                "oem":sorted({m.title() for m in OEM.findall(b)}),"body":b[:1200]})
seen=set();ded=[]
for x in sorted(out,key=lambda z:z['ts'],reverse=True):
    k=x['body'].lower()[:150]
    if k in seen: continue
    seen.add(k); ded.append(x)
cl=[x for x in ded if not({'DNC','UBEO_INCUMBENT','OWNS_EQUIPMENT'}&set(x['flags']))]
print("future-dated raw : %s   (stale/past dropped: %s)"%(format(len(out),','),format(stale,',')))
print("after dedup      : %s"%format(len(ded),','))
print("CLEAN actionable : %s"%format(len(cl),','))
for k,v in collections.Counter(x['src'] for x in cl).most_common(): print("   %-38s %s"%(k,format(v,',')))
print("   with OEM named %s"%sum(1 for x in cl if x['oem']))
json.dump(cl,open(OUT,"w"))
