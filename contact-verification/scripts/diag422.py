import json,subprocess,os
T=os.environ['TOKEN']
def call(m,url):
    o=subprocess.run(['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json',url],
        capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
def members(lid):
    ids=[];after=None
    while True:
        u="https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=250"+(("&after="+after) if after else "")
        q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
        after=(q.get('paging') or {}).get('next',{}).get('after')
        if not after: break
    return set(ids)
m422=members('422'); m4830=members('4830')
print("list 422 'HubSpot Tech Used - All':",len(m422))
print("list 4830 'ZoomInfo - Contacts'   :",len(m4830))
d=json.load(open('out_of_5243.json'))
from collections import Counter
c=Counter()
for x in d:
    a=x['cid'] in m422; b=x['cid'] in m4830
    k=("in422" if a else "OUT of 422")+" / "+("in4830" if b else "OUT of 4830")
    c[k]+=1
    x['in422']=a; x['in4830']=b
print("\nthe 46 movers no longer in 5243:")
for k,v in c.most_common(): print("   "+k.ljust(26)+str(v))
json.dump(d,open('out_of_5243.json','w'),indent=1)
print("\nexamples out of 422 (their NEW company has no 'uses HubSpot' signal):")
for x in d:
    if not x['in422']: print("   "+x['name'][:20].ljust(20)+str(x['co'])[:28])
