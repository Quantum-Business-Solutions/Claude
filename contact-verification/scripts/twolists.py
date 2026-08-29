import json,subprocess,os
T=os.environ['TOKEN']
def post(url,body):
    open('_tl.json','w').write(json.dumps(body))
    o=subprocess.run(['curl','-s','-X','POST','-H','Authorization: Bearer '+T,
        '-H','Content-Type: application/json','-d','@_tl.json',url],capture_output=True,text=True).stdout
    try: return json.loads(o)
    except Exception: return {"raw":o[:300]}
def mklist(name,*groups,**kw):
    """Each positional arg is one AND-group; the groups are OR'd together."""
    branchop=kw.get('branchop','AND')
    body={"name":name,"objectTypeId":"0-1","processingType":"DYNAMIC",
      "filterBranch":{"filterBranchType":"OR","filterBranchOperator":"OR","filters":[],
        "filterBranches":[{"filterBranchType":"AND","filterBranchOperator":branchop,
                           "filterBranches":[],"filters":g} for g in groups]}}
    r=post('https://api.hubapi.com/crm/v3/lists',body)
    lst=r.get('list') or {}
    if lst.get('listId'):
        print("CREATED  listId "+str(lst['listId']).ljust(6)+"  "+lst['name'])
        return str(lst['listId'])
    print("FAILED   "+name+": "+str(r.get('message'))[:220])
    return None

# ---- LIST A: contacts whose primary associated company we changed ----
# Primary filter is a DATE the mover pipeline stamps. The original filter was a substring inside
# ai__contact_evidence - capped at 990 chars with several writers appending, and a measured 22 of
# 70 movers had already lost the marker to truncation, silently emptying this list.
# The legacy substring stays as a second OR-group so movers written before ai__reassociated_on
# existed remain in the list until they are backfilled.
MOVED_DATE=[{"property":"ai__reassociated_on","filterType":"PROPERTY",
  "operation":{"operationType":"DATE_TIME","operator":"IS_KNOWN","includeObjectsWithNoValueSet":False}}]
MOVED_LEGACY=[{"property":"ai__contact_evidence","filterType":"PROPERTY",
  "operation":{"operationType":"STRING","operator":"CONTAINS","value":"RE-"+"ASSOCIATED",
               "includeObjectsWithNoValueSet":False}}]
# PROBE, do not assert. This file already refuses to guess a filter shape for "has no value"
# (below); a date operation this codebase has never used deserves the same treatment. Both groups
# go in ONE create request, so an unaccepted date shape would otherwise take the PROVEN legacy
# substring filter down with it and leave the highest-value output list simply not existing.
a=None
for shape in ({"operationType":"DATE_TIME","operator":"IS_KNOWN","includeObjectsWithNoValueSet":False},
              {"operationType":"ALL_PROPERTY","operator":"IS_KNOWN","includeObjectsWithNoValueSet":False},
              {"operationType":"DATE","operator":"IS_KNOWN","includeObjectsWithNoValueSet":False}):
    MOVED_DATE=[{"property":"ai__reassociated_on","filterType":"PROPERTY","operation":shape}]
    a=mklist("Claude - Moved Companies (primary company changed, LinkedIn verified)",
             MOVED_DATE, MOVED_LEGACY)
    if a: print("         (date filter shape accepted: "+shape["operationType"]+")"); break
if not a:
    print("WARN no accepted shape for ai__reassociated_on - falling back to the legacy substring "
          "ONLY. That filter loses movers to evidence truncation; fix the shape.")
    a=mklist("Claude - Moved Companies (primary company changed, LinkedIn verified)", MOVED_LEGACY)

# ---- LIST C: the human review queue, resident in HubSpot rather than a scratch file ----
c=None
for shape in ({"operationType":"ENUMERATION","operator":"IS_KNOWN","includeObjectsWithNoValueSet":False},
              {"operationType":"ALL_PROPERTY","operator":"IS_KNOWN","includeObjectsWithNoValueSet":False}):
    c=mklist("Claude - AI Verification Issues (needs a human)",
             [{"property":"ai__verification_issue","filterType":"PROPERTY","operation":shape}])
    if c: break
if not c: print("WARN could not create the AI Verification Issues list")

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
json.dump({"moved":a,"no_company":b,"issues":c},open('twolists.json','w'))
if not a or not b:
    import sys as _s
    print("HALT: an output list was not created - the pass produced no reviewable output."); _s.exit(2)
