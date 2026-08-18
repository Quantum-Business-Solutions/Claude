import json,subprocess,os,sys,re,urllib.parse
T=os.environ['TOKEN']
N=int(sys.argv[1]) if len(sys.argv)>1 else 6
def call(m,url,body=None):
    c=['curl','-s','-X',m,'-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open('_q3.json','w').write(json.dumps(body)); c+=['-d','@_q3.json']
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}
ids=[l.strip() for l in open('mem3675.txt') if l.strip()]
done=set()
if os.path.exists('li_verdicts_3675.json'):
    done={str(x['id']) for x in json.load(open('li_verdicts_3675.json'))}
def ident(u):
    if not u: return None
    m=re.search(r'/in/([^/?#]+)',u)
    return urllib.parse.quote(m.group(1)) if m else None
out=[]
for i in range(0,len(ids),100):
    chunk=[x for x in ids[i:i+100] if x not in done]
    if not chunk: continue
    b={"inputs":[{"id":x} for x in chunk],
       "properties":["firstname","lastname","company","jobtitle","hs_linkedin_url","linkedin_profile_url__unique_value"]}
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/read',b)
    for x in r.get('results',[]):
        p=x['properties']
        idn=ident(p.get('hs_linkedin_url')) or ident(p.get('linkedin_profile_url__unique_value'))
        out.append((x['id'],p.get('firstname'),p.get('lastname'),p.get('company'),p.get('jobtitle'),idn))
        if len(out)>=N: break
    if len(out)>=N: break
print("REMAINING (unverified):", len(ids)-len(done))
for cid,f,l,co,jt,idn in out:
    print(cid+" | "+str(f)+" "+str(l)+" | "+str(co)+" | "+str(jt)[:34]+" | "+str(idn))
