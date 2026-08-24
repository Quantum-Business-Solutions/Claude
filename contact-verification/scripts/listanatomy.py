#!/usr/bin/env python3
"""listanatomy.py <listId> - Phase 0 gate-chain mapper.

Membership in a calling list is rarely governed by that list alone. This walks the FULL
filter tree, recurses into every IN_LIST upstream gate, and reports every property that
can eject a contact - including ASSOCIATION filters that apply to the associated COMPANY.

Run this BEFORE the first write. It answers "what can drop someone off this list?" so a
later membership drop can be attributed instead of guessed at.

Writes list_anatomy_<listId>.json. Env: TOKEN."""
import json,sys, subprocess, os, sys

T = os.environ['TOKEN']
def get(url):
    o = subprocess.run(['curl','-s','--max-time','30','-H','Authorization: Bearer '+T, url],
                       capture_output=True, text=True).stdout
    try: return json.loads(o) if o.strip() else {}
    except Exception: return {}

def fetch(lid):
    d = get(f'https://api.hubapi.com/crm/v3/lists/{lid}?includeFilters=true')
    return d.get('list') or d

seen, gates, upstream = set(), [], []

def walk(branch, lid, depth=0, path='root'):
    """Recursively record every filter. Returns nothing; appends to `gates`."""
    btype = branch.get('filterBranchType')
    bop   = branch.get('filterBranchOperator')
    assoc = branch.get('associationTypeId')
    for f in branch.get('filters', []):
        ft = f.get('filterType')
        if ft == 'IN_LIST':
            sub = str(f.get('listId'))
            gates.append({'list': lid, 'path': path, 'kind': 'IN_LIST',
                          'detail': f'must ALSO be in list {sub}'})
            upstream.append((sub, lid))
        else:
            op = f.get('operation', {}) or {}
            gates.append({'list': lid, 'path': path,
                          'kind': 'ASSOCIATION(company)' if btype == 'ASSOCIATION' else 'PROPERTY',
                          'property': f.get('property'),
                          'operator': op.get('operator'),
                          'values': op.get('values') if op.get('values') is not None else op.get('value'),
                          'noValue': op.get('includeObjectsWithNoValueSet'),
                          'assocTypeId': assoc})
    for i, sb in enumerate(branch.get('filterBranches', [])):
        walk(sb, lid, depth+1, f'{path}>{(sb.get("filterBranchType") or "?")}[{i}]')

blockers = []
def process(lid):
    if lid in seen: return
    seen.add(lid)
    l = fetch(lid)
    name = l.get('name', '(unknown)')
    print(f'\n=== list {lid} :: {name} ===')
    print(f'    objectTypeId={l.get("objectTypeId")}  processingType={l.get("processingType")}')
    if l.get('objectTypeId') not in (None, '0-1'):
        print('    !! NOT a contact list - this process only runs on 0-1')
        blockers.append(f'list {lid} is objectTypeId {l.get("objectTypeId")}, not a contact list (0-1)')
    if lid == root and l.get('processingType') not in (None, 'DYNAMIC'):
        blockers.append(f'list {lid} is {l.get("processingType")}, not DYNAMIC - '
                        'this process is built for a list that recalculates')
    before = len(gates)
    walk(l.get('filterBranch') or {}, lid)
    for g in gates[before:]:
        if g['kind'] == 'IN_LIST':
            print(f'    [IN_LIST]     {g["detail"]}')
        else:
            tag = 'ASSOC(company)' if g['kind'].startswith('ASSOCIATION') else 'PROPERTY     '
            print(f'    [{tag}] {g.get("property")} {g.get("operator")} {str(g.get("values"))[:70]}')
    # recurse upstream
    for sub, parent in list(upstream):
        if sub not in seen: process(sub)

root = sys.argv[1]
process(root)

print('\n' + '='*72)
print('EVERY PROPERTY THAT CAN EJECT A CONTACT FROM LIST ' + root + ':')
props = {}
for g in gates:
    if g['kind'] == 'IN_LIST': continue
    key = (g.get('property'), g['kind'])
    props.setdefault(key, []).append(g['list'])
for (p, kind), lids in sorted(props.items(), key=lambda x: str(x[0])):
    where = 'on the CONTACT' if kind == 'PROPERTY' else 'on the ASSOCIATED COMPANY'
    print(f'  - {p:<34} {where:<26} (via list {"/".join(sorted(set(lids)))})')
print('\nupstream chain :', ' -> '.join([root] + [u[0] for u in upstream]) if upstream else root)
print('lists examined :', len(seen))
# (a) gates on a field this process is FORBIDDEN to write -> cleanly verified contacts stay invisible
warn = [p for (p, k) in props if p in ('hs_persona','jobtitle')]
if warn:
    print('\n!! WARNING: this list gates on ' + ', '.join(warn) + ' - fields this process must NOT write.')
    print('   A contact with a blank/wrong value there is invisible to the list no matter how cleanly verified.')
# (b) gates on a field this process DOES write -> the run changes membership underneath itself
WRITES = {'hs_lead_status','ai__li_still_at_company','ai__contact_evidence','ai__contact_verified_date',
          'ai__job_title','ai__sources_confirming','validated__linkedin_or_manually','hs_linkedin_url',
          'linkedin_profile_url__unique_value','company','phone','business_phone','email',
          'previous__company_domain_name'}
selfgate = sorted({p for (p, k) in props if p in WRITES})
if selfgate:
    print('\n!! this list gates on ' + ', '.join(selfgate) + ' - fields THIS PROCESS WRITES.')
    print('   Membership will change under the run: contacts ejected by our own writes stop being')
    print('   members, so they are never counted as unverified and never read. Measure coverage')
    print('   against the intake snapshot (mem_<listId>.txt), not against live membership.')
    if 'hs_lead_status' in selfgate:
        print('   hs_lead_status is the primary ejection mechanism - this is expected on a calling')
        print('   list, but the stop condition "unverified 0" is NOT proof the intake was covered.')
if blockers:
    print('\n!! PHASE 0 ABORT:')
    for b in blockers: print('   - ' + b)
    print('   Fix or pick a different list; do not run the batch loop against this one.')
json.dump({'root': root, 'lists': sorted(seen), 'gates': gates,
           'upstream': upstream}, open(f'list_anatomy_{root}.json','w'), indent=1)
print(f'\nwrote list_anatomy_{root}.json')
if blockers: sys.exit(3)
