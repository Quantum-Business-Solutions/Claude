import json,subprocess,os,datetime
T=os.environ['TOKEN']
cut=int(datetime.datetime(2026,7,18,tzinfo=datetime.timezone.utc).timestamp()*1000)
print("cutoff (30 days back) =",cut)
def search(body):
    open('_q3.json','w').write(json.dumps(body))
    o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,'-H','Content-Type: application/json',
      '-d','@_q3.json','https://api.hubapi.com/crm/v3/objects/contacts/search'],capture_output=True,text=True).stdout
    try:
        d=json.loads(o)
        return d.get('total') if 'total' in d else ('ERR '+json.dumps(d)[:120])
    except Exception: return o[:120]
F=lambda *f:{"filterGroups":[{"filters":list(f)}],"limit":1}
DATE={"propertyName":"ai__contact_verified_date","operator":"GTE","value":cut}
REASSOC={"propertyName":"ai__contact_evidence","operator":"CONTAINS_TOKEN","value":"*RE-ASSOCIATED*"}
GONE={"propertyName":"ai__li_still_at_company","operator":"EQ","value":"no"}
VERIFIED={"propertyName":"ai__li_still_at_company","operator":"HAS_PROPERTY"}
tests=[
 ("anything verified in the last 30 days", F(DATE)),
 ("A · re-associated to a new employer, verified in window", F(REASSOC,DATE)),
 ("B · verified GONE, destination not set, in window", F(GONE,DATE)),
 ("A or B (union = the real answer)", {"filterGroups":[{"filters":[REASSOC,DATE]},{"filters":[GONE,DATE]}],"limit":1}),
 ("total ever verified by this process", F(VERIFIED)),
]
for k,v in tests: print(str(search(v)).rjust(7)+"  "+k)
