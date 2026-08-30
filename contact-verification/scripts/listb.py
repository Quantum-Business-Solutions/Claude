import json,subprocess,os
T=os.environ['TOKEN']
def post(body):
    open('_lb.json','w').write(json.dumps(body))
    o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,
        '-H','Content-Type: application/json','-d','@_lb.json','https://api.hubapi.com/crm/v3/lists'],
        capture_output=True,text=True).stdout
    try: return json.loads(o)
    except Exception: return {"raw":o[:300]}
SHAPES=[
 ("NUMBER / IS_EQUAL_TO 0, include no-value",
  {"property":"number_of_associated_companies","filterType":"PROPERTY",
   "operation":{"operationType":"NUMBER","operator":"IS_EQUAL_TO","value":0,
                "includeObjectsWithNoValueSet":True}}),
 ("NUMBER / IS_LESS_THAN 1, include no-value",
  {"property":"number_of_associated_companies","filterType":"PROPERTY",
   "operation":{"operationType":"NUMBER","operator":"IS_LESS_THAN","value":1,
                "includeObjectsWithNoValueSet":True}}),
]
for label,f in SHAPES:
    body={"name":"Claude - No Primary Associated Company","objectTypeId":"0-1","processingType":"DYNAMIC",
      "filterBranch":{"filterBranchType":"OR","filterBranchOperator":"OR","filters":[],
        "filterBranches":[{"filterBranchType":"AND","filterBranchOperator":"AND","filterBranches":[],"filters":[f]}]}}
    r=post(body); lst=r.get('list') or {}
    if lst.get('listId'):
        print("CREATED  listId "+str(lst['listId'])+"   ("+label+")")
        json.dump({"no_company":str(lst['listId'])},open('listb.json','w'))
        break
    print("  .. rejected ("+label+"): "+str(r.get('message'))[:200])
