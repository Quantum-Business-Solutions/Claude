"""Unified decision-maker reading queue across all four engagement objects.

Ranked by where the decision-maker language actually sits. The rep's own
handwriting converts at 73% vs 62% overall, because a rep writes "DM is Chris M"
only when they have just been told exactly that - whereas an AI summary says
"decision maker" whenever the phrase came up.
"""
import json, os, re, time, urllib.request, collections
H = {'Authorization':'Bearer '+os.environ['PAT'], 'Content-Type':'application/json'}
def post(u,b):
    for i in range(6):
        try:
            r=urllib.request.Request(u,data=json.dumps(b).encode(),headers=H,method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return {}
        except Exception: time.sleep(2*(i+1))
    return {}

SPEC = [("calls","calls",["hs_call_body","hs_call_summary","hs_call_title","hs_timestamp"]),
        ("tasks","tasks",["hs_task_body","hs_task_subject","hs_timestamp"]),
        ("notes","notes",["hs_note_body","hs_timestamp"]),
        ("meetings","meetings",["hs_meeting_body","hs_meeting_title","hs_internal_meeting_notes","hs_timestamp"])]

def clean(t): return re.sub(r'\s+',' ', re.sub('<[^>]+>',' ', t or '')
                            .replace('&nbsp;',' ').replace('&amp;','&').replace('&#x27;',"'")).strip()

# the AI writes below these markers; everything above them is the rep's own hand
AI_MARK = re.compile(r'-{3,}\s*AI Generated Notes\s*-{3,}|\|\|\s*Summary\b|^\s*Summary\b', re.I)
def split_rep(t):
    m = AI_MARK.search(t)
    if not m: return t, ""          # no AI section at all - the whole thing is the rep
    return t[:m.start()], t[m.start():]

SHORTHAND = re.compile(r'\bDM\b|\bD\.M\.\b|\bPOC\b', re.I)
EXPLICIT  = re.compile(r'decision.?maker|decision.?makers|who decides|\bdecides\b|signs off|'
                       r'has to approve|makes (?:the|all) decisions', re.I)
AUTHORITY = re.compile(r'in charge of|handles the|handles their|responsible for|oversees|'
                       r'need to (?:speak|talk)|have to go through|referred? (?:me )?to|'
                       r'transferred (?:me )?to|put me through|is the (?:owner|president|CFO|CIO|director|administrator)|'
                       r'not the right person|not in charge|not my area|wrong person|who handles', re.I)
DEAD = ["no live person","speaker 1","automated greeting","welcome message","left a message",
        "left a voicemail","leave a message","standard greeting","not in service","mailbox is full",
        "office was closed","office is closed","unable to answer","attempted to reach",
        "attempted to contact","could not be completed","insufficient information",
        "no further details","enter some information","directing callers","press 1","did not answer",
        "no answer","call failure","dial by name","automated menu","voicemail prompt"]
SPOKE = re.compile(r"spoke (?:with|to)|s/w\b|talked to|\btt\b|\bsaid\b|advised|mentioned|told me|"
                   r"informed|connected w|transferred|referred|\bPOC\b|answered", re.I)

already = set()
import glob
for f in glob.glob("batch0*.json"):
    already |= {c["call"] for c in json.load(open(f))}
print("already read: %d" % len(already))

queue = []
for label, obj, props in SPEC:
    ids = json.load(open("dml_%s.json" % obj))
    ids = [i for i in ids if i not in already]
    got = 0
    for i in range(0, len(ids), 100):
        d = post("https://api.hubapi.com/crm/v3/objects/%s/batch/read" % obj,
                 {"properties":props, "inputs":[{"id":x} for x in ids[i:i+100]]})
        for r in d.get("results", []):
            p = r["properties"]
            txt = " || ".join(clean(p.get(k)) for k in props if k != "hs_timestamp" and p.get(k))
            if len(txt) < 60: continue
            low = txt.lower()
            if obj == "calls":
                # only calls carry dialer noise; a task or note is written on purpose
                if any(k in low for k in DEAD): continue
                if not SPOKE.search(txt): continue
            rep, ai = split_rep(txt)
            # TIER: where does the decision-maker language actually sit?
            if SHORTHAND.search(rep) and EXPLICIT.search(rep):  tier, why = 1, "rep shorthand, explicit DM"
            elif SHORTHAND.search(rep):                          tier, why = 2, "rep shorthand"
            elif EXPLICIT.search(rep):                           tier, why = 3, "rep wrote it out"
            elif EXPLICIT.search(txt):                           tier, why = 4, "AI notes, explicit DM"
            elif AUTHORITY.search(txt):                          tier, why = 5, "authority language only"
            else: continue
            queue.append({"id": r["id"], "obj": obj, "tier": tier, "why": why,
                          "ts": (p.get("hs_timestamp") or "")[:10], "text": txt[:1100],
                          "rep": rep.strip()[:400]})
            got += 1
        time.sleep(0.05)
    print("  %-9s %s of %s pooled records made the queue" % (label, format(got,","), format(len(ids),",")))

queue.sort(key=lambda x: (x["tier"], x["ts"] and -int(x["ts"].replace("-","")) or 0))
json.dump(queue, open("dm_queue_all.json","w"))
print()
print("="*62)
print("UNIFIED READING QUEUE: %s records" % format(len(queue), ","))
print("="*62)
for t in sorted({x["tier"] for x in queue}):
    n = [x for x in queue if x["tier"] == t]
    print("  tier %d  %-26s %-7s  %s" % (t, n[0]["why"], format(len(n),","),
          ", ".join("%s %d" % (k, v) for k, v in collections.Counter(x["obj"] for x in n).most_common())))
