import json,subprocess,os,re,unicodedata
NB=os.environ['NB']

def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode()
    return re.sub(r"[^a-z]","",s.lower())

# The universal set. Ordered by real-world prevalence so the first hit is usually the answer.
PATS=[
 ("first.last",    lambda f,l: f+"."+l),
 ("flast",         lambda f,l: f[0]+l),
 ("firstlast",     lambda f,l: f+l),
 ("first",         lambda f,l: f),
 ("first_last",    lambda f,l: f+"_"+l),
 ("f.last",        lambda f,l: f[0]+"."+l),
 ("firstl",        lambda f,l: f+l[0]),
 ("first-last",    lambda f,l: f+"-"+l),
 ("lastf",         lambda f,l: l+f[0]),
 ("last.first",    lambda f,l: l+"."+f),
 ("lastfirst",     lambda f,l: l+f),
 ("fl",            lambda f,l: f[0]+l[0]),
 ("last",          lambda f,l: l),
 ("f_last",        lambda f,l: f[0]+"_"+l),
]
NAMES=[p[0] for p in PATS]
BY={k:v for k,v in PATS}

def learn(samples):
    """samples [(first,last,email)] -> pattern names that explain a real sample, best first"""
    score={k:0 for k in NAMES}
    for fn,ln,em in samples:
        f,l=norm(fn),norm(ln)
        if not f or not l: continue
        local=em.split('@')[0].lower()
        for k in NAMES:
            try:
                if BY[k](f,l)==local: score[k]+=1
            except Exception: pass
    return [k for k in NAMES if score[k]>0]

def nb(email):
    o=subprocess.run(['curl','-s','--max-time','30',
        "https://api.neverbounce.com/v4/single/check?key="+NB+"&email="+email],
        capture_output=True,text=True).stdout
    try: return json.loads(o)
    except Exception: return {"status":"err"}

def resolve_all(first,last,domain,learned=None,nicknames=None):
    """Walk the FULL universal set (learned patterns first), plus nickname forms.
       Returns (email, (verdict, pattern), tried)."""
    f,l=norm(first),norm(last)
    if not f or not l: return None,None,[]
    order=[k for k in (learned or []) if k in NAMES]+[k for k in NAMES if k not in (learned or [])]
    firsts=[f]+[norm(n) for n in (nicknames or []) if norm(n) and norm(n)!=f]
    tried=[];catch=[];seen=set()
    for ff in firsts:
        for k in order:
            try: cand=BY[k](ff,l)+"@"+domain
            except Exception: continue
            if cand in seen: continue
            seen.add(cand)
            res=nb(cand).get('result')
            tried.append((cand,res,k+("" if ff==f else " ["+ff+"]")))
            if res=="valid": return cand,("valid",k+("" if ff==f else " nickname:"+ff)),tried
            if res=="catchall": catch.append((cand,k))
    if catch: return catch[0][0],("catchall",catch[0][1]),tried
    return None,None,tried

# common short forms, used only after the full set fails on the given name
NICK={
 "michael":["mike"],"michele":["shelly"],"michelle":["shelly"],"kristin":["kris"],"kristen":["kris"],
 "christopher":["chris"],"christine":["chris"],"jennifer":["jen","jenn"],"jessica":["jess"],
 "robert":["rob","bob"],"william":["will","bill"],"richard":["rick","rich"],"joseph":["joe"],
 "james":["jim","jamie"],"thomas":["tom"],"daniel":["dan"],"david":["dave"],"steven":["steve"],
 "stephen":["steve"],"matthew":["matt"],"nicholas":["nick"],"anthony":["tony"],"benjamin":["ben"],
 "samuel":["sam"],"samantha":["sam"],"katherine":["kate","katie","kathy"],"kathleen":["katie","kathy"],
 "elizabeth":["liz","beth"],"deborah":["deb","debbie"],"patricia":["pat","patty"],"susan":["sue"],
 "margaret":["maggie","meg"],"rebecca":["becky"],"alexander":["alex"],"alexandra":["alex"],
 "andrew":["andy","drew"],"edward":["ed"],"charles":["charlie","chuck"],"timothy":["tim"],
 "gregory":["greg"],"lawrence":["larry"],"douglas":["doug"],"frederick":["fred"],"theodore":["ted"],
 "vincent":["vince"],"lucinda":["lucy"],"allyson":["ally"],"stacie":["stacy"],"juliann":["julie","juli"],
}
def nicks(first):
    return NICK.get(norm(first),[])
