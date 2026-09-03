#!/usr/bin/env python3
"""recoverdest.py - recover a departed contact's destination from evidence already in HubSpot.

    TOKEN=... python3 recoverdest.py            # dry run: prints every extraction, writes nothing
    TOKEN=... python3 recoverdest.py --apply     # stamps ai__pending_mover_to

Why this exists. A `no` verdict means a profile was read and the CRM employer's row carried an end
date - and the SAME read almost always showed where the person went, because that is how you know
they left. Earlier passes wrote that fact into `ai__contact_evidence` as prose and never into a
field, so 446 contacts sit verified-departed with no destination anywhere, most with no company
association at all (a portal workflow detaches it 20 seconds after the ejection status is written).

The destination is therefore already paid for. Re-reading LinkedIn for it would spend 446 profile
reads to recover something we wrote down and then ignored. This parses it back out of the evidence
and stamps `ai__pending_mover_to`, after which moverqueue.py and movepipe.py do the rest.

Extraction is deliberately conservative, and prints EVERY match for a human to read before
--apply. Prose is not a schema: a regex over evidence strings written by a model on different days
will mis-read some of them, and a mis-read attaches a real person to a company that does not exist.
So: only these explicit "current row" phrasings, nothing inferred, a length sanity check, and a
stop-list of phrases that mean the opposite of a destination (own firm, career break, retired,
advisory only). Anything that does not match cleanly is left for a re-read - that is the correct
outcome, not a failure."""
import os,sys,json,re,subprocess,tempfile
T=os.environ['TOKEN']; APPLY='--apply' in sys.argv[1:]
TMP=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False).name
def call(m,url,body=None):
    c=['curl','-s','--max-time','30','-w','\n%{http_code}','-X',m,
       '-H','Authorization: Bearer '+T,'-H','Content-Type: application/json']
    if body is not None:
        open(TMP,'w').write(json.dumps(body)); c+=['-d','@'+TMP]
    o=subprocess.run(c+[url],capture_output=True,text=True).stdout
    txt,_,code=o.rpartition('\n'); code=code.strip()
    if not code.isdigit() or not code.startswith('2'):
        sys.stderr.write('HTTP '+code+' :: '+txt[:200]+'\n'); sys.exit(2)
    return json.loads(txt) if txt.strip() else {}
# Only phrasings that NAME a current employer. Each captures the company up to the title/date.
PATS=[re.compile(p,re.I) for p in (
  # Highest confidence first: an explicit destination the earlier pass wrote as a conclusion.
  r"\bmover\s*->\s*((?:[^;(\n.]|\.(?=\w))+?)\s*(?:\(|;|$|\.\s|\.$)",
  r"current row:\s*(.{2,60}?)\s+(?:from\s+\d{4}|,\s*|\bfrom\b)",
  r"current operating row:\s*(.{2,60}?)\s+(?:from\s+\d{4}|,\s*|\bfrom\b)",
  r"current corporate row:\s*(.{2,60}?)\s+(?:from\s+\d{4}|,\s*|\bfrom\b)",
  r"current end-null row:\s*(.{2,60}?)\s+(?:from\s+\d{4}|,\s*|\bfrom\b)",
  r"current operating employer:\s*(.{2,60}?)\s*,",
  r"\bnow at\s+(.{2,60}?)\s*[:,]",
  # "now VP Global Channel & Partner Sales at Demand AI" - a title, then `at`, then the employer.
  r"\bnow\s+[A-Za-z][^;\n]{0,55}?\s+at\s+([A-Z](?:[^;,.\n]|\.(?=\w)){1,45}?)\s*(?:[;,]|\.\s|\.$|$)",
  # "now Everforth, Executive Vice Chairman since 03/2025" / "now Filmore Co-Founder since 07/2025"
  r"\bnow\s+([A-Z][\w&.'/\-]*(?:\s+[A-Z][\w&.'/\-]*){0,3})\s*,?\s+[^;,\n]{2,50}?\s+since\s+\d",
)]
# Phrases that mean "no destination", so a company-looking capture nearby must NOT be trusted.
STOP=("own firm","own vehicle","own consultancy","own company","self-employed","fractional",
      "career break","retired","retirement","no end-null operating","no current operating",
      "board member","advisory only","no operating role","portfolio operator","only end-null",
      # The decision-maker era. A verdict `no` reached by reasoning about seniority is not a
      # departure at all, and mining a destination out of it propagates the original error - the
      # person may never have left. 112 of the 455 read this way; they need re-verifying, not
      # re-associating. Adam Riggs is the proof: "Regional Sales Manager at Adams Remco (end null)
      # - still there but NOT the owner ... not a decision-maker" was banked as `no`.
      "not a decision-maker","not a decision maker","non-ceo","not the owner","staff role",
      "not an icp","decision-maker","not decision maker","still there",
      # their own vehicle, by any name. Terri Delfino's "Now Strategic Marketing Advisor at her
      # own T.Delfino Consulting Services" and Brian Zatulove's "Stealth/own-venture destinations
      # are not associable company records" both slipped through the first list.
      "her own","his own","their own","own-venture","own venture","stealth","independent consultant",
      "not associable","solo ","personal investing","personal brand")
TRAIL=re.compile(r"[\s,;:.\-|(]+$")
# A capture routinely carries the date range, a parenthetical or a second role after the employer
# name. Cut at whichever of these appears first; everything after it is not the company.
CUT=re.compile(r"\s+(?:since|from|in)\s+\d|\s*\(|\s+\+\s|\s*\d{1,2}/\d{4}|\s+end-null|"
               r"\s*\)|\s+\(current\)",re.I)
# Titles are not employers. A capture that IS one, or ends in a dangling preposition, is a
# mis-parse - "-> Founder" and "-> VP of Marketing at" both came out of the first draft of this.
TITLES=re.compile(r"^(?:a\s+|an\s+|the\s+)?(?:founder|co-founder|ceo|coo|cto|cro|cmo|cfo|president|"
                  r"owner|partner|principal|advisor|adviser|consultant|director|manager|"
                  r"vice president|vp|svp|evp|head|chief|chair|chairman|board member|"
                  r"managing director|general manager|marketing consultant)\b",re.I)
DANGLE=re.compile(r"\b(?:at|in|of|for|with|to|and|&)$",re.I)
def clean(c):
    c=(c or '').strip()
    m=CUT.search(c)
    if m: c=c[:m.start()]
    c=TRAIL.sub('',c.strip())
    c=re.sub(r"^(the\s+)?",'',c,flags=re.I).strip()
    return c
# A negation immediately before a company name means the person is NOT there. The first version of
# this file read "NOT at Digital Hands", "No longer CEO at Laborie" and "LEFT NRI North America" as
# DESTINATIONS, and three real contacts were then attached to the employer they had just left, with
# the verdict flipped from no to yes, validated__linkedin_or_manually stamped Yes and lead status
# set to ConnectandSell Prospect. One of them carried "Do not call at NRI" in the same field. That
# is worse than doing nothing: it hands an SDR a dial at the company the person left, and marks it
# as verified on the way out so nobody re-checks it.
NEGATION=re.compile(r"(?:\bnot\b|\bno longer\b|\bnever\b|\bleft\b|\bleaving\b|\bdeparted\b|"
                    r"\bdeparting\b|\bdo not call\b|\bex-|\bformer(?:ly)?\b|\bresigned\b|"
                    r"\bexited\b|\bout at\b|\bno current\b|\bended\b|ENDED)",re.I)
POSITIVE=re.compile(r"(?:\bnow\b|\bcurrent(?:ly)?\b|\bpresent\b|end.null|\bjoined\b|"
                    r"\bjoining\b|\bsince\b|mover\s*->|\bmoved to\b|\bnew employer\b)",re.I)
def negated(e,start):
    """Is the capture governed by a negation rather than by a 'now/current' marker?

    NEAREST MARKER WINS. Two earlier attempts at this were wrong in opposite directions and both
    are worth remembering, because the shapes recur:

    - Judging on the whole evidence string flags nearly every genuine mover, since "LEFT <old>,
      then <x>, now <new>" contains a negation by construction.
    - Judging on "a positive anywhere in the left window beats a negation" let a distant "Now board
      chair roles only" excuse an adjacent "No longer CEO at Laborie", and re-attached a man to the
      company he had left.

    So scan backwards and take whichever marker sits CLOSEST to the capture. Note the regexes
    deliberately spell their own word boundaries: a trailing \b in an alternation silently kills
    any branch ending in a non-word character, which is how `mover\s*->` never matched and a real
    destination was rejected as negated."""
    w=e[max(0,start-90):start]
    n=[m.end() for m in NEGATION.finditer(w)]
    q=[m.end() for m in POSITIVE.finditer(w)]
    if not n: return False
    if not q: return True
    return max(n)>max(q)      # the negation is the closer of the two
def extract(ev):
    e=ev or ''
    for p in PATS:
        m=p.search(e)
        if not m: continue
        if negated(e,m.start(1)):
            return (None,"the capture sits behind a negation (%r) - this names the employer they "
                         "LEFT, not where they went"%e[max(0,m.start(1)-46):m.start(1)].strip()[-46:])
        co=clean(m.group(1))
        # A negation INSIDE the capture is decisive regardless of what precedes it: "NOT at Digital
        # Hands" is not the name of an employer. Checked separately from the surrounding context
        # because a positive marker can sit immediately before it ("Current row: NOT at ...").
        if NEGATION.search(co):
            return (None,"the capture %r contains a negation - it is not an employer name"%co[:40])
        if not (3<=len(co)<=60): return (None,"capture %r failed the length check"%co[:40])
        if TITLES.match(co): return (None,"capture %r is a job title, not an employer"%co[:40])
        if DANGLE.search(co): return (None,"capture %r ends mid-phrase"%co[:40])
        # a capture that is mostly lowercase words is prose, not a company name
        if co.islower() and len(co.split())>1: return (None,"capture %r reads as prose"%co[:40])
        if not re.search(r"[A-Za-z]{3}",co): return (None,"capture %r has no real word"%co[:40])
        window=e[max(0,m.start()-160):m.end()+160].lower()
        hit=[s for s in STOP if s in window]
        if hit: return (None,"%r sits beside %r - that is not an employer to attach"%(co[:30],hit[0]))
        return (co,None)
    return (None,"no 'current row' phrasing in the evidence")
rows=[];after=None
while True:
    b={"filterGroups":[{"filters":[
        {"propertyName":"ai__li_still_at_company","operator":"EQ","value":"no"},
        {"propertyName":"ai__pending_mover_to","operator":"NOT_HAS_PROPERTY"},
        {"propertyName":"ai__reassociated_on","operator":"NOT_HAS_PROPERTY"}]}],
       "properties":["firstname","lastname","ai__contact_evidence","company","associatedcompanyid",
                     "hs_lead_status"],"limit":100}
    if after: b["after"]=after
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/search',b)
    rows+=r.get('results',[]); after=((r.get('paging') or {}).get('next') or {}).get('after')
    if not after: break
print("departed with no destination recorded: %d\n"%len(rows))
got=[];miss=[]
for x in rows:
    p=x['properties']
    who=((p.get('firstname') or '')+' '+(p.get('lastname') or '')).strip()
    co,why=extract(p.get('ai__contact_evidence'))
    (got if co else miss).append({"id":x['id'],"who":who,"newco":co,"why":why,
                                  "was":p.get('company'),"ls":p.get('hs_lead_status')})
for g in got: print("  FOUND   %-13s %-24s -> %s"%(g['id'],g['who'][:24],g['newco']))
print()
from collections import Counter
wc=Counter((m['why'] or '').split(' -')[0].split(' ')[0:2].__str__() for m in miss)
print("NOT RECOVERED %d, by reason:"%len(miss))
for k,v in wc.most_common(8): print("   %-46s %d"%(k[:46],v))
json.dump(got,open('recovered.json','w'),indent=1)
json.dump(miss,open('needs_reread.json','w'),indent=1)
print("\nrecovered %d -> recovered.json | needs a LinkedIn re-read %d -> needs_reread.json"
      %(len(got),len(miss)))
if not APPLY:
    print("\nDRY RUN - nothing written. Read the FOUND list above, then re-run with --apply.")
    sys.exit(0)
ok=0
for i in range(0,len(got),100):
    ch=got[i:i+100]
    r=call('POST','https://api.hubapi.com/crm/v3/objects/contacts/batch/update',
      {"inputs":[{"id":g['id'],"properties":{"ai__pending_mover_to":g['newco'][:200]}} for g in ch]})
    ok+=len(r.get('results',[]))
print("\nstamped ai__pending_mover_to on %d contact(s)"%ok)
print("next: moverqueue.py then movepipe.py - and every destination still gets the same treatment,")
print("      resolved to one named company with a domain or queued for a human.")
