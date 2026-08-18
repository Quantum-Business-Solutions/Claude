import json,subprocess,os,re
T=os.environ['TOKEN']
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_r32.json','w').write(json.dumps(body)); c+=['-d','@_r32.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
def dig(s):
    d=re.sub(r"\D","",s or "")
    if len(d)==11 and d.startswith("1"): d=d[1:]
    return d

# SELF-TEST FIRST: prove the query works on a case we already know the answer to.
# Nancy Elsner's old business_phone (212) 991-6540 is TouchTunes' number - whosephone.py found it.
def owner(d):
    """try every stored format, the way whosephone.py does"""
    if not d or len(d)<7: return None
    forms=[d, d[:3]+"-"+d[3:6]+"-"+d[6:], "("+d[:3]+") "+d[3:6]+"-"+d[6:],
           "+1"+d, d[:3]+"."+d[3:6]+"."+d[6:]]
    for pat in forms:
        r=call('POST','https://api.hubapi.com/crm/v3/objects/companies/search',
          {"filterGroups":[{"filters":[{"propertyName":"phone","operator":"CONTAINS_TOKEN","value":"*"+pat+"*"}]}],
           "properties":["name","phone"],"limit":5})
        for x in r.get('results',[]):
            if dig(x['properties'].get('phone'))==d:
                return x['properties'].get('name')
    return None

KNOWN="2129916540"   # TouchTunes
t=owner(KNOWN)
print("SELF-TEST on a known-positive ((212) 991-6540 = TouchTunes): "+str(t))
if not t:
    print("SELF-TEST FAILED - the query cannot find a number we know is there.")
    print("Refusing to draw any conclusion from its silence. Stopping.")
    raise SystemExit(1)
print("self-test passed, so a null result below is now meaningful\n")

m=json.load(open('mismatch32.json'))
res=[]
for x in m:
    d=dig(x['business_phone'])
    own=owner(d)
    same=own and (x['co'] or '').lower()[:10] in str(own).lower()
    verdict=("SAME company, alternate line" if same else
             ("WRONG COMPANY -> "+str(own) if own else "no company record holds this number"))
    res.append(dict(x,owner=own,verdict=verdict))
    print("  "+str(x['name'])[:19].ljust(19)+str(x['co'])[:20].ljust(20)+str(x['business_phone'])[:16].ljust(16)+verdict)
json.dump(res,open('mismatch32_redone.json','w'),indent=1)
wrong=[r for r in res if r['owner'] and not ((r['co'] or '').lower()[:10] in str(r['owner']).lower())]
print()
print("CONFIRMED wrong-company numbers on the calling list: "+str(len(wrong)))
for w in wrong: print("   "+w['name']+" at "+str(w['co'])+" holds "+str(w['owner'])+"'s number")
