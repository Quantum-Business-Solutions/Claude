"""Are the acquired dealers' email domains still alive, and where does their mail go?

Shawn's question: the old addresses may still work because acquirers forward. NeverBounce
cannot answer it - 44 of the 98 addresses sit on catch-all domains, where 'valid' is
meaningless. The MX record answers it directly:
  MX at the acquirer's infrastructure -> mail is being routed to the acquirer; the old address
                                        still reaches a real tray
  MX present, independent             -> the acquired business still runs its own mail
  no MX                               -> the domain accepts no mail at all; the address is dead
"""
import json, re, time
import dns.resolver
S='/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
BY=json.load(open(S+'/acquired_domain_contacts.json'))

res=dns.resolver.Resolver()
res.lifetime=6; res.timeout=6
def mx(d):
    try:
        return sorted(str(r.exchange).rstrip('.').lower() for r in res.resolve(d,'MX'))
    except dns.resolver.NXDOMAIN: return ['_NXDOMAIN']
    except dns.resolver.NoAnswer: return ['_NO_MX']
    except Exception as e: return ['_ERR:'+type(e).__name__]

# fingerprint the acquirers' own mail hosts so "routes to the acquirer" can be recognised
ACQ_DOMAINS={'Xerox':'xerox.com','Xerox Business Solutions':'xeroxbusinesssolutions.com',
 'Visual Edge':'visualedgeit.com','Visual Edge Technology / Visual Edge, Inc.':'visualedgeit.com',
 'Flex Technology Group':'flextg.com','Applied Imaging':'appliedimaging.com',
 'Novatech':'novatech.net','DEX Imaging':'deximaging.com','Konica Minolta':'kmbs.konicaminolta.us',
 'UBEO':'ubeo.com','EO Johnson':'eojohnson.com','SumnerOne':'sumnerone.com',
 'Marco':'marconet.com','Impact Networking':'impactmybiz.com','Function4':'function-4.com'}
acqmx={}
for k,d in ACQ_DOMAINS.items():
    acqmx[k]=mx(d); time.sleep(0.05)
print("acquirer mail hosts, for fingerprinting:")
for k,v in acqmx.items(): print(f"   {k[:34]:36} {v[:2]}")

def hostroot(h):
    p=h.split('.')
    return '.'.join(p[-3:]) if len(p)>=3 else h

print(f"\nchecking {len(BY)} acquired domains...\n")
rows=[]
for dom,people in sorted(BY.items(), key=lambda x:-len(x[1])):
    recs=mx(dom)
    acqr=(people[0].get('acquirer') or '').strip()
    verdict='unknown'
    detail=''
    if recs[0].startswith('_NXDOMAIN'):
        verdict='DEAD - domain does not exist'
    elif recs[0].startswith('_NO_MX'):
        verdict='DEAD - no mail server'
    elif recs[0].startswith('_ERR'):
        verdict='lookup failed'
    else:
        joined=' '.join(recs)
        # does it point at the acquirer's own mail infrastructure?
        target=acqmx.get(acqr) or []
        hit=[h for h in recs if any(hostroot(h)==hostroot(t) for t in target if not t.startswith('_'))]
        if hit:
            verdict='FORWARDS TO ACQUIRER'; detail=hit[0]
        elif re.search(r'\b(xerox|konicaminolta|ricoh|canon|kyocera|toshiba)\b', joined):
            verdict='FORWARDS TO A MANUFACTURER/ACQUIRER'; detail=recs[0]
        elif re.search(r'outlook|office365|protection\.outlook|google|googlemail|barracuda|'
                       r'mimecast|proofpoint|appriver|intermedia|reflexion', joined):
            verdict='LIVE - own mail (hosted)'; detail=recs[0]
        else:
            verdict='LIVE - own mail'; detail=recs[0]
    print(f"  {dom:34} {len(people):2}c  {verdict:38} {detail[:34]}")
    rows.append({'domain':dom,'contacts':len(people),'acquirer':acqr,'mx':recs,
                 'verdict':verdict,'detail':detail,
                 'people':[{'id':p['id'],'name':p['name'],'email':p['email'],'title':p['title'],
                            'nb':p['nb'],'company':p['company'],'company_id':p['company_id']}
                           for p in people]})
    time.sleep(0.05)
json.dump(rows, open(S+'/acquired_domain_mx.json','w'), indent=1)
from collections import Counter
print("\n=== SUMMARY ===")
c=Counter(r['verdict'] for r in rows)
for k,v in c.most_common():
    n=sum(r['contacts'] for r in rows if r['verdict']==k)
    print(f"  {k:40} {v:3} domains, {n:3} contacts")
