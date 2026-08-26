import json,re,datetime
today=datetime.date(2026,8,26)
def clean(t): return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',t or '').replace('&nbsp;',' ').replace('&amp;','&').replace('&#x27;',"'").replace('&quot;','"')).strip()
MON={m.lower():i+1 for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'])}
for a,i in list(MON.items()): MON[a[:3]]=i
W={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'twelve':12,'eighteen':18,'a':1,'another':1}
def n2(s):
    s=str(s).lower().strip()
    return W.get(s) if s in W else (float(s) if re.match(r'^\d+(\.\d+)?$',s) else None)
ABS=re.compile(r'(?:lease|contract|agreement)[^.]{0,50}?(?:expires?|ends?|is up|due|up|does not end until|doesn\'?t end until|runs? (?:out|to|through|until))\s*(?:in|on|around|end of|until|til|till)?\s*([A-Za-z]+)?\s*(\d{1,2})?[/-]?(\d{1,2})?[/-]?(\d{2,4})',re.I)
REM=[re.compile(r'\b(\d+(?:\.\d+)?|one|two|three|four|five|six|eighteen|twelve)\s*(?:more\s+)?(yrs?|years?|months?|mos?)\s*(?:left|remaining|to go)\b',re.I),
     re.compile(r'\b(?:has|have|got)\s+(?:about\s+|around\s+|roughly\s+)?(\d+(?:\.\d+)?|one|two|three|four|five|six)\s*(yrs?|years?|months?|mos?)\b(?=[^.]{0,25}(?:left|remaining|to go|on (?:the |their )?(?:lease|contract)))',re.I)]
INTO=re.compile(r'\b(\d+(?:\.\d+)?|one|two|three|four|five)\s*(?:yrs?|years?)?\s+into\s+(?:a|their|the)?\s*(\d+)\s*(?:yrs?|years?)\b',re.I)
SIGNED=re.compile(r'\b(?:just|recently|newly)\s+(?:signed|renewed|re-?signed)|\bsigned\s+(?:a\s+)?new\b|\brenewed\s+(?:their|our|the)\b',re.I)
SIGTERM=re.compile(r'\b(\d+|three|four|five|six|seven)\s*(?:yr|yrs|year|years)\b',re.I)
AGO=re.compile(r'\b(?:last year|a year ago|(\d+)\s*(?:yrs?|years?)\s+ago|back in (\d{4}))\b',re.I)
UBEO=re.compile(r'\blease\s+with\s+us\b|\bwith us that expires\b|\bwe sold\b|\bsold off lease\b|\bthrough us\b|\bcurrent customer\b|\bwith us\b|\bfrom us\b|\bour lease\b',re.I)
DNC=re.compile(r'\bXDNC\b|\bDO NOT CALL\b|\bstop calling\b|\bdnc\b',re.I)
OWN=re.compile(r'\b(?:they |we )?own (?:their|our|the|them|it)\b|\bpurchased (?:their|the|them|it) (?:copier|printer|equipment|machine)|\bowns? (?:their|the) (?:copier|equipment|machine)|\bbought (?:their|the)\b',re.I)
OEM=re.compile(r'\b(Ricoh|Xerox|Canon|Konica(?:\s+Minolta)?|Minolta|Sharp|Toshiba|Kyocera|Lanier|Savin|Muratec|Lexmark|Brother|Epson)\b',re.I)
AUTOREN=re.compile(r'\bauto(?:matic)?[- ]?renew\w*|\bevergreen\b',re.I)
def absd(b):
    m=ABS.search(b)
    if not m: return None,None
    mo,d1,d2,y=m.groups()
    try:
        if y is None: return None,None
        y=int(y); y=y+2000 if y<100 else y
        if not (2024<=y<=2040): return None,None
        return datetime.date(y,MON.get((mo or '').lower()) or (int(d1) if d1 and 1<=int(d1)<=12 else 1),1),m.group(0)
    except: return None,None
def addy(base,yrs): 
    try: return base.replace(year=base.year+int(yrs)) if float(yrs)==int(yrs) else base+datetime.timedelta(days=int(365*float(yrs)))
    except: return base+datetime.timedelta(days=int(365*float(yrs)))
def remd(b,base):
    for rx in REM:
        m=rx.search(b)
        if not m: continue
        n=n2(m.group(1))
        if n is None: continue
        u=m.group(2).lower()
        return (base+datetime.timedelta(days=int(30*n)) if u.startswith(('mo','month')) else addy(base,n)),m.group(0)
    m=INTO.search(b)
    if m:
        el,tot=n2(m.group(1)),n2(m.group(2))
        if el is not None and tot and tot>el: return addy(base,tot-el),m.group(0)
    return None,None
def sigd(b,base):
    if not SIGNED.search(b): return None,None
    m=SIGTERM.search(b)
    if not m: return None,None
    n=n2(m.group(1))
    if not n or not (2<=n<=7): return None,None
    start=base
    a=AGO.search(b)
    if a:
        if a.group(1): start=addy(base,-float(a.group(1)))
        elif a.group(2):
            try: start=datetime.date(int(a.group(2)),1,1)
            except: pass
        else: start=addy(base,-1)
    return addy(start,n),f"{m.group(0)} term, signed {start.strftime('%m/%Y')}"

out=[]
for fn,obj,bodyprops,tsp in [("v2_calls.json","call",["hs_call_body","hs_call_summary"],"hs_timestamp"),
                             ("v2_notes.json","note",["hs_note_body"],"hs_timestamp")]:
    pool=json.load(open(fn))
    for rid,r in pool.items():
        p=r["properties"]
        parts=[clean(p.get(k)) for k in bodyprops if clean(p.get(k))]
        b=" || ".join(parts)
        if len(b)<25: continue
        ts=(p.get(tsp) or "")[:10]
        try: base=datetime.date(*map(int,ts.split("-")))
        except: continue
        flags=[]
        if DNC.search(b): flags.append("DNC")
        if UBEO.search(b): flags.append("UBEO_INCUMBENT")
        if OWN.search(b) and not re.search(r'\blease',b,re.I): flags.append("OWNS_EQUIPMENT")
        if AUTOREN.search(b): flags.append("AUTO_RENEW")
        e,basis=absd(b); src="stated date"
        if not e: e,basis=remd(b,base); src="computed from remaining term"
        if not e: e,basis=sigd(b,base); src="computed from just-signed"
        if not e or e<today: continue
        out.append({"engagement_id":rid,"engagement_type":obj,"ts":ts,"end":e.isoformat(),
                    "basis":basis,"src":src,"flags":flags,
                    "oem":sorted({m.title() for m in OEM.findall(b)}),"body":b[:1200]})
seen={};ded=[]
for x in sorted(out,key=lambda z:(z['ts']),reverse=True):
    k=x['body'].lower()[:150]
    if k in seen: continue
    seen[k]=1; ded.append(x)
print(f"raw signal records      : {len(out)}")
print(f"after dedup             : {len(ded)}")
import collections
print("\nby source:"); 
for k,v in collections.Counter(x['src'] for x in ded).items(): print(f"   {k:32} {v}")
print("\nby type:")
for k,v in collections.Counter(x['engagement_type'] for x in ded).items(): print(f"   {k:32} {v}")
print("\nflags:")
for k,v in collections.Counter(f for x in ded for f in x['flags']).items(): print(f"   {k:32} {v}")
clean_set=[x for x in ded if not({'DNC','UBEO_INCUMBENT','OWNS_EQUIPMENT'}&set(x['flags']))]
print(f"\n►► CLEAN actionable (excl DNC/UBEO-incumbent/owns): {len(clean_set)}")
print(f"   with incumbent OEM named : {sum(1 for x in clean_set if x['oem'])}")
print(f"   expiring within 12 months: {sum(1 for x in clean_set if x['end']<=(today+datetime.timedelta(days=365)).isoformat())}")
json.dump(clean_set,open("v2_clean.json","w")); json.dump(ded,open("v2_all.json","w"))
