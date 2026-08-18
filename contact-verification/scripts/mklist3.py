import json,subprocess,os
T=os.environ['TOKEN']
def post(url,body):
    open('_m3.json','w').write(json.dumps(body))
    o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,
        '-H','Content-Type: application/json','-d','@_m3.json',url],capture_output=True,text=True).stdout
    try: return json.loads(o)
    except Exception: return {"raw":o[:300]}
DATEF={"property":"ai__contact_verified_date","filterType":"PROPERTY",
  "operation":{"operationType":"ROLLING_DATE_RANGE","operator":"IS_AFTER","numberOfDays":30,
               "includeObjectsWithNoValueSet":False}}
REASSOC={"property":"ai__contact_evidence","filterType":"PROPERTY",
  "operation":{"operator":"CONTAINS","value":"RE-ASSOCIATED","operationType":"STRING","includeObjectsWithNoValueSet":False}}
GONE={"property":"ai__li_still_at_company","filterType":"PROPERTY",
  "operation":{"operator":"IS_ANY_OF","values":["no"],"operationType":"ENUMERATION","includeObjectsWithNoValueSet":False}}
body={"name":"Verified Company Change - Last 30 Days (Claude)","objectTypeId":"0-1","processingType":"DYNAMIC",
  "filterBranch":{"filterBranchType":"OR","filterBranchOperator":"OR","filters":[],
    "filterBranches":[
      {"filterBranchType":"AND","filterBranchOperator":"AND","filterBranches":[],"filters":[REASSOC,DATEF]},
      {"filterBranchType":"AND","filterBranchOperator":"AND","filterBranches":[],"filters":[GONE,DATEF]}]}}
r=post('https://api.hubapi.com/crm/v3/lists',body)
lst=r.get('list') or {}
if lst.get('listId'):
    lid=str(lst['listId'])
    print("CREATED  listId "+lid+"  |  "+lst['name']+"  |  "+lst['processingType'])
    json.dump({"listId":lid},open('newlist.json','w'))
else:
    print("FAILED: "+json.dumps(r)[:300])
