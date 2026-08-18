import json,sys,os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'.')
from patmail import learn,resolve
g=json.load(open('email_gap.json'))
samples=json.load(open('domain_samples.json'))
pat={d:learn(v) for d,v in samples.items()}
json.dump(pat,open('domain_patterns.json','w'),indent=1)
targets=[v for v in g['need']+g['noemail'] if v['codom'] in samples]
def work(t):
    nm=(t.get('name') or '').split()
    if len(nm)<2: return None
    em,verdict,tried=resolve(nm[0],nm[-1],t['codom'],pat.get(t['codom'],[]))
    return dict(cid=t['cid'],name=t['name'],codom=t['codom'],coname=t['coname'],
        old=t.get('email'),email=em,verdict=verdict[0] if verdict else None,
        pattern=verdict[1] if verdict else None,
        tried=[{"e":a,"r":b,"p":c} for a,b,c in tried])
with ThreadPoolExecutor(max_workers=6) as ex:
    out=[r for r in ex.map(work,targets) if r]
json.dump(out,open('email_found.json','w'),indent=1)
print("done",len(out))
