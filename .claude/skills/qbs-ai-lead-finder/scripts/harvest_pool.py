import json,os,time,urllib.request
PAT=os.environ['PAT']
def post(u,b,t=6):
    for i in range(t):
        try:
            r=urllib.request.Request(u,data=json.dumps(b).encode(),
              headers={'Authorization':f'Bearer {PAT}','Content-Type':'application/json'},method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(2*(i+1)); continue
            return {}
    return {}
BASE=["years left","yrs left","just signed","went with","one year","two years","three years","four years",
 "2027","2028","2029","2030","2031","lease","leasing","leased","leases","contract","contracting","contracts",
 "1 year","2 years","3 years","4 years","5 years",".5 years","comes up in","few years","already have","expires",
 "expiration","exp.","expiring","remaining","happy with","comes due","term","left on"]
NEW=["*months left*","*months remaining*","*months to go*","*months on*","*18 months*","*24 months*","*36 months*",
 "*60 month*","*60 mo*","*36 month*","*48 month*","*63 month*","*66 month*","*39 month*",
 "*auto renew*","*automatic renew*","*evergreen*","*end of term*","*term end*","*buyout*","*90 day*","*notice*",
 "*up for renewal*","*coming due*","*comes up*","*expire*","*renews*",
 "*just renewed*","*recently signed*","*just re-signed*","*signed a new*","*renewed their*","*renewed our*",
 "Ricoh","Xerox","Canon","Konica","Minolta","Toshiba","Kyocera","Sharp","Lanier","Savin","Lexmark","Muratec"]
TERMS=BASE+NEW
def harvest(obj,props,searchprops):
    pool={}
    for prop in searchprops:
        for t in TERMS:
            after=None;n=0
            while True:
                b={"limit":200,"properties":props,
                   "filterGroups":[{"filters":[{"propertyName":prop,"operator":"CONTAINS_TOKEN",
                     "value":t if t.startswith("*") or " " not in t else f'"{t}"'}]}]}
                if after: b["after"]=after
                d=post(f"https://api.hubapi.com/crm/v3/objects/{obj}/search",b)
                rs=d.get("results",[])
                if not rs: break
                for r in rs: pool.setdefault(r["id"],r)
                n+=len(rs)
                after=(d.get("paging") or {}).get("next",{}).get("after")
                if not after or n>=9800: break
                time.sleep(0.06)
            time.sleep(0.06)
    return pool
calls=harvest("calls",["hs_call_body","hs_call_summary","hs_call_title","hs_timestamp"],["hs_call_body","hs_call_summary"])
print("calls pool :",len(calls)); json.dump(calls,open("v2_calls.json","w"))
notes=harvest("notes",["hs_note_body","hs_timestamp"],["hs_note_body"])
print("notes pool :",len(notes)); json.dump(notes,open("v2_notes.json","w"))
print("TOTAL      :",len(calls)+len(notes))
