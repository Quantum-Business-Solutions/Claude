import json,os,time,urllib.request,collections,socket
socket.setdefaulttimeout(60)
PAT=os.environ['PAT']

def post(u,b):
    for i in range(6):
        try:
            r=urllib.request.Request(u,data=json.dumps(b).encode(),
              headers={'Authorization':'Bearer '+PAT,'Content-Type':'application/json'},method='POST')
            return json.load(urllib.request.urlopen(r)),None
        except urllib.error.HTTPError as e:
            body=e.read().decode()[:150]
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return None,"%s %s"%(e.code,body)
        except Exception:
            time.sleep(2*(i+1))
    return None,"retries"

cust=set(json.load(open("customer_engagement_ids.json")))
FILES={"call":("call_clean_v10.json","calls"),
       "task":("task_clean_v10.json","tasks"),
       "email":("email_clean_v10.json","emails"),
       "meeting":("meeting_clean_v10.json","meetings"),
       "note":("note_clean_v10.json","notes")}

total=0
for typ,(fn,obj) in FILES.items():
    rows=json.load(open(fn))
    hit=[x['engagement_id'] for x in rows if x['engagement_id'] in cust]
    if not hit:
        print("  %-9s none"%obj); continue
    ok=0
    for i in range(0,len(hit),100):
        d,e=post("https://api.hubapi.com/crm/v3/objects/%s/batch/update"%obj,
                 {"inputs":[{"id":x,"properties":{"ai__lease_information":""}} for x in hit[i:i+100]]})
        if e: print("   ERR",obj,e)
        else: ok+=len(d.get("results",[]))
        time.sleep(0.25)
    # drop from the local signal set so future rollups never see them
    keep=[x for x in rows if x['engagement_id'] not in cust]
    json.dump(keep,open(fn,"w"))
    print("  %-9s cleared %-5s  signal set %s -> %s"%(obj,format(ok,','),format(len(rows),','),format(len(keep),',')))
    total+=ok
print("\ncleared %s engagement records on customer companies"%format(total,','))
