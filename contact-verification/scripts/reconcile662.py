import json,subprocess,os
from collections import Counter
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_rc.json','w').write(json.dumps(body)); c+=['-d','@_rc.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def members(lid):
    ids=[];after=None
    while True:
        u="https://api.hubapi.com/crm/v3/lists/"+lid+"/memberships?limit=250"+(("&after="+after) if after else "")
        q=call('GET',u); ids+=[str(x['recordId']) for x in q.get('results',[])]
        after=(q.get('paging') or {}).get('next',{}).get('after')
        if not after: break
    return set(ids)

orig=[l.strip() for l in open('mem5243.txt') if l.strip()]
now=members('5243')
m422=members('422'); m4830=members('4830')
gone=[x for x in orig if x not in now]
print("ORIGINAL 5243: "+str(len(orig)))
print("NOW in 5243  : "+str(len(now))+"   (still there from the original: "+str(len([x for x in orig if x in now]))+")")
print("LEFT the list: "+str(len(gone)))

OKP={'persona_3','persona_11','persona_8'}
OKL={'CAS - No Pitch - Quick Hang Up','ConnectandSell Prospect'}
info={}
for i in range(0,len(gone),100):
    b={"inputs":[{"id":x} for x in gone[i:i+100]],
       "properties":["firstname","lastname","company","hs_persona","hs_lead_status","mobilephone","phone",
                     "business_phone","lifecyclestage","ai__li_still_at_company","jobtitle"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]): info[x['id']]=x['properties']

reasons=Counter(); primary=Counter(); detail=[]
for cid in gone:
    p=info.get(cid)
    if p is None: primary['record deleted or unreadable']+=1; continue
    rs=[]
    if (p.get('hs_lead_status') or '') not in OKL: rs.append("lead status = "+str(p.get('hs_lead_status')))
    if (p.get('hs_persona') or '') not in OKP: rs.append("persona = "+str(p.get('hs_persona')))
    if not (p.get('mobilephone') or p.get('phone') or p.get('business_phone')): rs.append("no phone")
    if (p.get('lifecyclestage') or '') in ('other','customer'): rs.append("lifecycle = "+str(p.get('lifecyclestage')))
    if cid not in m422: rs.append("not in 422 HubSpot-tech")
    if cid not in m4830: rs.append("not in 4830 ZoomInfo-tech")
    for z in rs: reasons[z.split(' = ')[0]]+=1
    # attribute a single primary cause, in the order that actually explains the drop
    if any(r.startswith('lead status') for r in rs): primary['lead status changed (my verdict)']+=1
    elif "not in 4830 ZoomInfo-tech" in rs: primary['left ZoomInfo-tech list (re-association)']+=1
    elif "not in 422 HubSpot-tech" in rs: primary['left HubSpot-tech list']+=1
    elif any(r.startswith('persona') for r in rs): primary['persona changed']+=1
    elif "no phone" in rs: primary['phone removed']+=1
    elif any(r.startswith('lifecycle') for r in rs): primary['lifecycle changed']+=1
    else: primary['STILL MEETS EVERY CRITERION - unexplained']+=1
    detail.append({"cid":cid,"name":str(p.get('firstname'))+" "+str(p.get('lastname')),
                   "co":p.get('company'),"jt":p.get('jobtitle'),"flag":p.get('ai__li_still_at_company'),
                   "lead":p.get('hs_lead_status'),"persona":p.get('hs_persona'),
                   "in422":cid in m422,"in4830":cid in m4830,"reasons":rs})
print("\nPRIMARY reason each of the "+str(len(gone))+" left:")
for k,v in primary.most_common(): print("   "+str(v).rjust(4)+"  "+k)
print("\nevery failing criterion counted (a contact can fail several):")
for k,v in reasons.most_common(): print("   "+str(v).rjust(4)+"  "+k)
json.dump(detail,open('gone_from_5243.json','w'),indent=1)
# lead status breakdown
lc=Counter(d['lead'] for d in detail if any(r.startswith('lead status') for r in d['reasons']))
print("\nof those whose lead status now disqualifies them:")
for k,v in lc.most_common(): print("   "+str(v).rjust(4)+"  "+str(k))
# what did I verify them as?
fc=Counter(d['flag'] for d in detail)
print("\nmy LinkedIn verdict on the ones that left:")
for k,v in fc.most_common(): print("   "+str(v).rjust(4)+"  "+str(k))
