import json,subprocess,os
T=os.environ['TOKEN']
body={"filterGroups":[{"filters":[
  {"propertyName":"ai__contact_evidence","operator":"CONTAINS_TOKEN","value":"*NOT-MKT*"}]}],
 "properties":["firstname","lastname","company","hs_lead_status","ai__li_still_at_company"],"limit":100}
open('_n.json','w').write(json.dumps(body))
o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,'-H','Content-Type: application/json',
 '-d','@_n.json','https://api.hubapi.com/crm/v3/objects/contacts/search'],capture_output=True,text=True).stdout
r=json.loads(o)
res=r.get('results',[])
print("contacts carrying the [NOT-MKT] marker:",r.get('total'))
prospect=[]
for x in res:
    p=x['properties']
    ls=p.get('hs_lead_status')
    nm=str(p.get('firstname'))+' '+str(p.get('lastname'))
    print("  "+nm[:24].ljust(24)+str(p.get('company'))[:24].ljust(24)+"lead="+str(ls))
    if ls=='ConnectandSell Prospect': prospect.append(nm)
print("\nNOT-MKT people the workflow has flipped back to Prospect:",len(prospect))
for n in prospect: print("   ",n)
