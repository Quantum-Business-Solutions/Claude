import json,subprocess,os,re,sys,unicodedata
NB=os.environ['NB']

def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode()
    return re.sub(r"[^a-z]","",s.lower())

PATS={
 "first.last": lambda f,l: f"{f}.{l}",
 "flast":      lambda f,l: f"{f[0]}{l}",
 "first":      lambda f,l: f"{f}",
 "firstlast":  lambda f,l: f"{f}{l}",
 "firstl":     lambda f,l: f"{f}{l[0]}",
 "f.last":     lambda f,l: f"{f[0]}.{l}",
 "first_last": lambda f,l: f"{f}_{l}",
 "lastfirst":  lambda f,l: f"{l}{f}",
 "last.first": lambda f,l: f"{l}.{f}",
 "firstlastinit":lambda f,l: f"{f}{l[0]}",
}

def learn(samples):
    """samples: [(first,last,email)] -> ordered list of pattern names by evidence"""
    score={k:0 for k in PATS}
    for fn,ln,em in samples:
        f,l=norm(fn),norm(ln)
        if not f or not l: continue
        local=em.split('@')[0].lower()
        for k,fn2 in PATS.items():
            try:
                if fn2(f,l)==local: score[k]+=1
            except Exception: pass
    return [k for k,v in sorted(score.items(),key=lambda x:-x[1]) if v>0]

def nb(email):
    o=subprocess.run(['curl','-s','--max-time','30',
        f"https://api.neverbounce.com/v4/single/check?key={NB}&email={email}"],
        capture_output=True,text=True).stdout
    try: return json.loads(o)
    except Exception: return {"status":"err","raw":o[:120]}

def resolve(first,last,domain,pats,extra_fallback=True):
    """return (email,nb_result,tried) or (None,...)"""
    f,l=norm(first),norm(last)
    if not f or not l: return None,None,[]
    order=list(pats)
    if extra_fallback:
        for k in ("first.last","flast","firstlast","first"):
            if k not in order: order.append(k)
    tried=[];catchalls=[]
    for k in order:
        cand=PATS[k](f,l)+"@"+domain
        if cand in [t[0] for t in tried]: continue
        r=nb(cand); res=r.get('result')
        tried.append((cand,res,k))
        if res=="valid": return cand,("valid",k),tried
        if res=="catchall": catchalls.append((cand,k))
    if catchalls: return catchalls[0][0],("catchall",catchalls[0][1]),tried
    return None,None,tried
