import json,subprocess,os
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_g.json','w').write(json.dumps(body)); c+=['-d','@_g.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
def members(lid):
    ids=[];after=None
    while True:
        u="https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=250"+(("&after="+after) if after else "")
        q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
        after=(q.get('paging') or {}).get('next',{}).get('after')
        if not after: break
    return set(ids)
m5243=members('5243'); m8260=members('8260')
print("5243:",len(m5243)," 8260:",len(m8260))
rows=json.load(open('stale_marker.json'))
for r in rows:
    print(r['name'][:18].ljust(18)+" in5243="+str(r['cid'] in m5243).ljust(6)+" in8260="+str(r['cid'] in m8260))
# how many re-associated movers are still in 5243 at all?
L=json.load(open('reassoc_log.json'))
mv=[(r.get('id') or r.get('cid')) for r in L]
print("\nre-associated movers still in list 5243: "+str(len([x for x in mv if x in m5243]))+" of "+str(len(set(mv))))
