import json, re, sys
d=json.load(open('/home/user/Claude/davinci-private-label/content/praxera_faqs.json'))
posts=json.load(open('/tmp/posts29.json'))

# Mindy's rule: Praxera must never be portrayed as manufacturing.
# "manufactured in the U.S." / "cGMP facility" are explicitly approved.
BAN=[
 (r"\bwe manufacture|\bwe produce\b|\bwe formulate\b|\bwe make (?:the|our|these) (?:product|supplement|formula)",
  "first-person manufacturing claim"),
 (r"praxera\s+(?:manufactures|produces|formulates|makes)", "Praxera portrayed as manufacturer"),
 (r"\bour (?:manufacturing|facility|facilities|plant|lab|laboratory|production)\b", "first-person facility claim"),
 (r"\bin-house (?:manufactur|production|formulat)", "in-house production claim"),
 (r"\bmanufactured by praxera\b", "manufactured-by-Praxera claim"),
 (r"\bwe (?:offer|provide|do) custom (?:formulation|formulas)", "custom formulation offered as our service"),
 (r"\bour custom (?:formulation|formula)", "custom formulation as our service"),
 (r"davinci|da vinci|vetriscience|pettech|pet tech", "other-brand mention"),
 (r"davincilabs\.com|pl-demo", "other-brand / demo link"),
 (r"\b(?:cures?|treats?|prevents?|diagnoses?)\s+(?:a\s+|an\s+|the\s+)?\w*\s*(?:disease|illness|condition|cancer|diabetes)", "disease claim"),
 (r"\bwill (?:cure|treat|prevent|heal)\b", "disease claim"),
 (r"\bTri-Mag|DIMPRO|Daily Best|Mega Probiotic|All-Zyme|Hair Effects|Collagen Bright|DygloFit|Ubiquinol™|Enzyme Benefits|GI Benefits|Candid-Away|Mito-Fuel|Maxi-BCAA|Cocoa HGH",
  "branded product name from the legacy catalog"),
]
WARN=[(r"custom formulation|custom formula", "mentions custom formulation - verify framed as industry concept only"),
      (r"guarantee|guaranteed", "absolute claim"),
      (r"\bFDA[- ]approved\b", "FDA-approved wording (supplements are not FDA-approved)")]

viol=[]; warn=[]
for pid, items in d.items():
    for qi,(q,a) in enumerate(items,1):
        blob=q+' '+a
        low=blob.lower()
        for pat,label in BAN:
            for m in re.finditer(pat, low, re.I):
                viol.append((pid,qi,label,blob[max(0,m.start()-45):m.end()+45]))
        for pat,label in WARN:
            for m in re.finditer(pat, low, re.I):
                warn.append((pid,qi,label,blob[max(0,m.start()-45):m.end()+45]))

print("=== BLOCKING VIOLATIONS:", len(viol))
for v in viol: print("  [%s q%d] %s\n      ...%s..."%v)
print("\n=== WARNINGS (review, not blocking):", len(warn))
for w in warn: print("  [%s q%d] %s\n      ...%s..."%w)

# structural checks
bad=[]
for pid,items in d.items():
    if pid not in posts: bad.append((pid,'not in target set'))
    for q,a in items:
        if not q.strip().endswith('?'): bad.append((pid,'question missing ?: '+q[:50]))
        if len(a)<90: bad.append((pid,'answer too short: '+a[:50]))
        if len(a)>700: bad.append((pid,'answer too long'))
        if 'Question goes here' in q or 'Answer goes here' in a: bad.append((pid,'placeholder text'))
print("\n=== STRUCTURAL ISSUES:", len(bad))
for b in bad: print("  ",b)
print("\ncoverage: %d posts / %d target posts"%(len(d),len(posts)))
