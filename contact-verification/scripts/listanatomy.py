#!/usr/bin/env python3
"""listanatomy.py <listId> - Phase 0 gate-chain mapper.

Membership in a calling list is rarely governed by that list alone. This walks the FULL
filter tree, recurses into every IN_LIST upstream gate, and reports every property that
can eject a contact - including ASSOCIATION filters that apply to the associated COMPANY.

Run this BEFORE the first write. It answers "what can drop someone off this list?" so a
later membership drop can be attributed instead of guessed at.

Writes list_anatomy_<listId>.json. Env: TOKEN."""
import json, subprocess, os, sys

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

def process(lid):
    if lid in seen: return
    seen.add(lid)
    l = fetch(lid)
    name = l.get('name', '(unknown)')
    print(f'\n=== list {lid} :: {name} ===')
    print(f'    objectTypeId={l.get("objectTypeId")}  processingType={l.get("processingType")}')
    if l.get('objectTypeId') not in (None, '0-1'):
        print('    !! NOT a contact list - this process only runs on 0-1')
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
warn = [p for (p, k) in props if p in ('hs_persona','jobtitle')]
if warn:
    print('\n!! WARNING: this list gates on ' + ', '.join(warn) + ' - fields this process must NOT write.')
    print('   A contact with a blank/wrong value there is invisible to the list no matter how cleanly verified.')
json.dump({'root': root, 'lists': sorted(seen), 'gates': gates,
           'upstream': upstream}, open(f'list_anatomy_{root}.json','w'), indent=1)
print(f'\nwrote list_anatomy_{root}.json')
