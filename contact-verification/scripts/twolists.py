import json,subprocess,os
T=os.environ['TOKEN']
def post(url,body):
    open('_tl.json','w').write(json.dumps(body))
    o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,
        '-H','Content-Type: application/json','-d','@_tl.json',url],capture_output=True,text=True).stdout
    try: return json.loads(o)
    except Exception: return {"raw":o[:300]}
def mklist(name,filters,branchop="AND"):
    body={"name":name,"objectTypeId":"0-1","processingType":"DYNAMIC",
      "filterBranch":{"filterBranchType":"OR","filterBranchOperator":"OR","filters":[],
        "filterBranches":[{"filterBranchType":"AND","filterBranchOperator":branchop,
                           "filterBranches":[],"filters":filters}]}}
    r=post('https://api.hubapi.com/crm/v3/lists',body)
    lst=r.get('list') or {}
    if lst.get('listId'):
        print("CREATED  listId "+str(lst['listId']).ljust(6)+"  "+lst['name'])
        return str(lst['listId'])
    print("FAILED   "+name+": "+str(r.get('message'))[:220])
    return None

# ---- LIST A: contacts whose primary associated company we changed ----
MOVED={"property":"ai__contact_evidence","filterType":"PROPERTY",
  "operation":{"operationType":"STRING","operator":"CONTAINS","value":"RE-ASSOCIATED",
               "includeObjectsWithNoValueSet":False}}
a=mklist("Claude - Moved Companies (primary company changed, LinkedIn verified)",[MOVED])

# ---- LIST B: contacts with no primary associated company ----
# probe the right shape for "has no value"
SHAPES=[
 ("ALL_PROPERTY / IS_UNKNOWN",
  {"property":"associatedcompanyid","filterType":"PROPERTY",
   "operation":{"operationType":"ALL_PROPERTY","operator":"IS_UNKNOWN","includeObjectsWithNoValueSet":True}}),
 ("NUMBER / IS_UNKNOWN",
  {"property":"associatedcompanyid","filterType":"PROPERTY",
   "operation":{"operationType":"NUMBER","operator":"IS_UNKNOWN","includeObjectsWithNoValueSet":True}}),
 ("STRING / IS_UNKNOWN",
  {"property":"associatedcompanyid","filterType":"PROPERTY",
   "operation":{"operationType":"STRING","operator":"IS_UNKNOWN","includeObjectsWithNoValueSet":True}}),
]
b=None
for label,f in SHAPES:
    b=mklist("Claude - No Primary Associated Company",[f])
    if b:
        print("   (shape used: "+label+")")
        break
json.dump({"moved":a,"no_company":b},open('twolists.json','w'))
