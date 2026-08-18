import json
from collections import Counter
intake=[l.strip() for l in open('mem5243.txt') if l.strip()]
verd={str(x['id']):x['verdict'] for x in json.load(open('li_verdicts.json'))}
have=[c for c in intake if c in verd]
miss=[c for c in intake if c not in verd]
print("intake snapshot (mem5243.txt)      : "+str(len(intake)))
print("of those, carrying a verdict       : "+str(len(have)))
print("of those, NEVER verified           : "+str(len(miss)))
print()
print("verdict log total                  : "+str(len(verd)))
print("  verdicts for contacts NOT in the intake snapshot: "+str(len([k for k in verd if k not in set(intake)])))
print()
print("verdict mix across the whole log   : "+str(dict(Counter(verd.values()))))
u=sum(1 for v in verd.values() if v=='unreadable')
print("unreadable, whole log              : "+str(u)+" of "+str(len(verd))+"  = "+str(round(100*u/len(verd),1))+"%")
json.dump(miss,open('never_verified.json','w'))
