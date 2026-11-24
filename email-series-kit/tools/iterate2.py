import json,subprocess,os,re
from hs_model import render
import bind
new=open('template_new.html').read()
base=json.load(open('emails_before.json'))
ks={}      # (eid:module, ei) -> k
state={}   # same key -> {'best':(score,k),'tried':set,'done':bool}
def cap_of(key,default): return 2 if default==1 else 4
def build(ks):
    em=[bind.apply(e,ks) for e in base]
    os.makedirs('all2',exist_ok=True)
    for e in em: open('all2/%s.html'%e['id'],'w').write(render(new,e))
    return em
def default_k(eid,mod,ei):
    html=[e for e in base if e['id']==eid][0]['content']['widgets'][mod]['body']['html']
    els=list(bind.EL.finditer(html))
    return 1 if bind.kind(els[ei].group(1))=='big' else 2
for rnd in range(6):
    em=build(ks)
    subprocess.run("NODE_PATH=$(npm root -g) node evalw2.js all2",shell=True,check=True,capture_output=True)
    sc=json.load(open('all2_scores.json'))
    unresolved=0
    for eid,v in sc.items():
        for ek in set(v['d'])|set(v['m']):
            mi,ei=ek.split('|'); mi=int(mi); ei=int(ei)
            mod='module-%d-0-0'%mi
            key=(eid+':'+mod,ei)
            score=v['d'].get(ek,0)*1+v['m'].get(ek,0)*1
            st=state.setdefault(key,{'best':None,'tried':set(),'dk':default_k(eid,mod,ei)})
            cur=ks.get(key,st['dk'])
            st['tried'].add(cur)
            if st['best'] is None or score<st['best'][0]: st['best']=(score,cur)
            if score==0: continue
            cap=2 if st['dk']==1 else 4
            cands=[c for c in [cur+1,cur-1,cur+2,cur-2,0,1,2,3,4] if 0<=c<=cap and c not in st['tried']]
            if cands: ks[key]=cands[0]; unresolved+=1
            else: ks[key]=st['best'][1]
    print('round',rnd,'to retry',unresolved,flush=True)
    if unresolved==0: break
# final: best per element
final={}
for key,st in state.items(): final[key]=st['best'][1]
em=build(final)
subprocess.run("NODE_PATH=$(npm root -g) node evalw2.js all2",shell=True,check=True,capture_output=True)
sc=json.load(open('all2_scores.json'))
bad=sum(1 for v in sc.values() for t in 'dm' for x in v[t].values() if x>0)
brk=sum(1 for v in sc.values() for t in 'dm' for x in v[t].values() if x>=100)
print('final bad elements (desktop+mobile)',bad,'broken/overflow',brk)
json.dump(em,open('emails_after.json','w'))
json.dump({'%s|%d'%k:v for k,v in final.items()},open('ks_final.json','w'))
print('final saved')
