import json,subprocess,os
from collections import Counter
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_w.json','w').write(json.dumps(body)); c+=['-d','@_w.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    return json.loads(o) if o.strip() else {}
ids=[];after=None
while True:
    u="https://api.hubapi.com/crm/v3/lists/5243/memberships?limit=250"+(("&after="+after) if after else "")
    q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
    after=(q.get('paging') or {}).get('next',{}).get('after')
    if not after: break
m5243=set(ids)
L=json.load(open('reassoc_log.json'))
mv=sorted({(r.get('id') or r.get('cid')) for r in L})
out=[x for x in mv if x not in m5243]
print("movers NOT in list 5243:",len(out))
OKP={'persona_3','persona_11','persona_8'}
OKL={'CAS - No Pitch - Quick Hang Up','ConnectandSell Prospect'}
reasons=Counter(); detail=[]
for i in range(0,len(out),100):
    b={"inputs":[{"id":x} for x in out[i:i+100]],
       "properties":["firstname","lastname","company","hs_persona","hs_lead_status","mobilephone",
                     "phone","business_phone","lifecyclestage","ai__li_still_at_company"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']; rs=[]
        if (p.get('hs_persona') or '') not in OKP: rs.append("persona="+str(p.get('hs_persona')))
        if (p.get('hs_lead_status') or '') not in OKL: rs.append("lead="+str(p.get('hs_lead_status')))
        if not (p.get('mobilephone') or p.get('phone') or p.get('business_phone')): rs.append("NO PHONE")
        if (p.get('lifecyclestage') or '') in ('other','customer'): rs.append("lifecycle="+p['lifecyclestage'])
        for z in rs: reasons[z.split('=')[0] if '=' in z else z]+=1
        detail.append({"cid":x['id'],"name":str(p.get('firstname'))+' '+str(p.get('lastname')),
                       "co":p.get('company'),"reasons":rs,"flag":p.get('ai__li_still_at_company')})
print("\nwhy they are out (a contact can have more than one reason):")
for k,v in reasons.most_common(): print("   "+k.ljust(12)+str(v))
json.dump(detail,open('out_of_5243.json','w'),indent=1)
print("\nsample:")
for d in detail[:14]: print("   "+d['name'][:20].ljust(20)+str(d['co'])[:20].ljust(20)+", ".join(d['reasons'])[:66])
