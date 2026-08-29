"""Roll engagement-level decision-maker findings up to the CONTACT record.

Two things land on a contact:
  1. a VERDICT on their buying authority, with the evidence behind it
  2. a STATUS FLAG when a conversation says they have gone, retired, changed
     role, or asked not to be called

Never writes hs_buying_role. Conflicting verdicts across calls are surfaced as
conflicts, not silently resolved - a person who disclaims authority on one call
and is named the decision maker on another is a question, not a fact.
"""
import json, os, re, glob, time, datetime, urllib.request, collections
from resolver import resolve, candidates, score, norm, H

PORTAL = "516382"
RANK = {"Decision Maker": 4, "Shares Authority": 3, "Gatekeeper": 2,
        "Not the Decision Maker": 2, "Unclear": 1}
CONFRANK = {"CONFIRMED": 2, "STATED": 1, None: 0}

# my own markers, written deliberately in caps so they are machine-readable later
STATUS = [
 (r"LOGGED CONTACT NO LONGER AT COMPANY|LOGGED CONTACT GONE|NO LONGER AT THE SCHOOL", "No Longer At Company"),
 (r"LOGGED CONTACT RETIRED|RETIRED SEVERAL YEARS AGO|RETIREE", "Retired"),
 (r"LOGGED CONTACT NOT KNOWN AT COMPANY|NOT KNOWN AT COMPANY|LOGGED CONTACT NOT FINDABLE|NOT IN THEIR SYSTEM|CONTACT NOT KNOWN", "Not Known At Company"),
 (r"REASSIGNED|CHANGED ROLES|HAS CHANGED ROLES", "Role Changed"),
 (r"WRONG NUMBER|STALE NUMBER", "Wrong Number"),
 (r"NO DIRECT LINE|EMAIL ONLY|NO PHONE NUMBER AVAILABLE", "Email Only - No Phone"),
 (r"RARELY ON SITE|only goes in person briefly|TRAVELS BETWEEN OFFICES", "Rarely On Site"),
]
OPTOUT = re.compile(r"OPT-OUT REQUESTED|removed from the call list|taken off the call list|"
                    r"no more soliciting|not to be called|asked to be removed", re.I)
# who asked to opt out - the sentence names them
OPT_WHO = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:requested|has requested|asked)\b", re.I)

cases = []
for f in sorted(glob.glob("batch*.json")) + sorted(glob.glob("fix0*.json")):
    for c in json.load(open(f)): c["_src"] = f; cases.append(c)
# later files win for the same call (fixes supersede)
byc = {}
for c in cases: byc[c["call"]] = c
cases = list(byc.values())
print("engagement determinations: %d" % len(cases))

verdicts = collections.defaultdict(list)   # contact_id -> [determination]
flags    = collections.defaultdict(list)   # contact_id -> [(flag, evidence, date)]

def nm(p): return ("%s %s" % (p.get("firstname") or "", p.get("lastname") or "")).strip()

for n, c in enumerate(cases, 1):
    cands, direct = candidates(c["call"], c.get("obj","calls"))
    byid = {x["id"]: x for x in cands}
    dm_id = None
    if c.get("dm"):
        dm_id, _role_state, crm_name, _s = resolve(c["dm"], c["call"], cands, c.get("obj","calls"))
        if dm_id:
            verdicts[dm_id].append(dict(
                verdict="Decision Maker", conf=c["conf"], role=c.get("role"),
                ev=c["ev"], why=c["why"], call=c["call"], logged=c["logged"], name=crm_name))
    # the contact the call is logged against, when it is NOT the decision maker
    for cid in direct:
        if cid == dm_id: continue
        p = (byid.get(cid) or {}).get("properties", {})
        low = (c["ev"] + " " + c["why"]).lower()
        if c.get("dm"):
            gate = bool(re.search(r"gatekeeper|receptionist|assistant|transferred|switchboard|front desk|operator|answered the (call|phone)", low))
            v = "Gatekeeper" if gate else "Not the Decision Maker"
        elif re.search(r"not the decision.?maker|disclaims authority|not in charge|not her area|not his area|"
                       r"does not (make|handle)|not responsible", low):
            v = "Not the Decision Maker"
        else:
            continue
        verdicts[cid].append(dict(verdict=v, conf=None, role=None, ev=c["ev"], why=c["why"],
                                  call=c["call"], logged=c["logged"], name=nm(p)))
    # status flags - attribute to the LOGGED contact only, since that is who the marker describes
    txt = c["ev"] + " " + c["why"]
    for rx, lab in STATUS:
        if re.search(rx, txt):
            for cid in direct: flags[cid].append((lab, txt, c["call"], c["logged"]))
            break
    # opt-outs - attribute to whoever the sentence actually names
    if OPTOUT.search(txt):
        who = None
        m = OPT_WHO.search(txt)
        if m: who = m.group(1)
        target = None
        if who:
            best = 0
            for x in cands:
                s = score(who, x["properties"].get("firstname"), x["properties"].get("lastname"))
                if s > best: best, target = s, x["id"]
            if best < 2: target = None
        if target is None and len(direct) == 1: target = direct[0]
        if target: flags[target].append(("Opt-Out Requested", txt, c["call"], c["logged"]))
    if n % 40 == 0: print("  ...%d/%d" % (n, len(cases)), flush=True)

print("contacts with a verdict : %d" % len(verdicts))
print("contacts with a flag    : %d" % len(flags))

def d8(s):
    m, d, y = s.split("/"); return "%s-%s-%s" % (y, m, d)

writes = {}
conflicts = 0
for cid, ds in verdicts.items():
    ds.sort(key=lambda x: (RANK.get(x["verdict"],0), CONFRANK.get(x["conf"],0), d8(x["logged"])), reverse=True)
    top = ds[0]
    kinds = {x["verdict"] for x in ds}
    conflict = "Decision Maker" in kinds and ("Not the Decision Maker" in kinds or "Gatekeeper" in kinds)
    verdict = "Unclear" if conflict else top["verdict"]
    if conflict: conflicts += 1
    head = "%s" % verdict
    if top.get("conf"): head += " [%s]" % top["conf"]
    if top.get("role"): head += " - " + top["role"]
    body = "%s - %s ** %s [source: call id %s, logged %s]" % (head, top["ev"], top["why"], top["call"], top["logged"])
    if len(ds) > 1:
        body += "\n\nCORROBORATION - %d engagements support a verdict on this person:" % len(ds)
        for x in ds[1:6]:
            body += "\n  - %s (%s, call %s): %s" % (x["verdict"], x["logged"], x["call"], x["why"][:150])
    if conflict:
        body = ("*** CONFLICTING EVIDENCE - one engagement names this person the decision maker and "
                "another has them disclaiming authority. Resolve before acting. ***\n\n") + body
    p = {"ai__decision_maker": body[:65000],
         "ai__decision_maker_verdict": verdict,
         "ai__decision_maker_evidence_count": len(ds),
         "ai__decision_maker_last_evidence": d8(max(x["logged"] for x in ds))}
    if top.get("conf") and not conflict: p["ai__decision_maker_confidence"] = top["conf"]
    if top.get("role"): p["ai__decision_maker_role"] = top["role"][:255]
    writes[cid] = p

# A contact who has left, retired, or is unknown at the company cannot be a
# gatekeeper or a decision maker - the verdict is meaningless and the status
# flag carries the whole meaning. Without this the classifier reads "Pedro
# transferred me" and labels the RETIRED contact a gatekeeper.
GONE = {"No Longer At Company", "Retired", "Not Known At Company", "Wrong Number"}
for cid, fs in flags.items():
    if any(f[0] in GONE for f in fs) and cid in writes:
        w = writes[cid]
        if w.get("ai__decision_maker_verdict") in ("Gatekeeper", "Not the Decision Maker"):
            w["ai__decision_maker_verdict"] = "Unclear"
            w.pop("ai__decision_maker_confidence", None)
            w["ai__decision_maker"] = ("NO VERDICT - this contact is flagged as gone from the company, so "
                                       "their buying authority is moot. See the status flag.\n\n") + w["ai__decision_maker"]

for cid, fs in flags.items():
    fs.sort(key=lambda x: d8(x[3]), reverse=True)
    lab, txt, call, logged = fs[0]
    p = writes.setdefault(cid, {})
    p["ai__contact_status_flag"] = lab
    p["ai__contact_status_evidence"] = ("%s [source: call id %s, logged %s]" % (txt, call, logged))[:65000]

print("conflicting verdicts    : %d" % conflicts)
print("contact records to write: %d" % len(writes))
json.dump(writes, open("contact_writes.json","w"))

items = [{"id":k, "properties":v} for k,v in writes.items()]
ok = 0
for i in range(0, len(items), 100):
    r = urllib.request.Request("https://api.hubapi.com/crm/v3/objects/contacts/batch/update",
        data=json.dumps({"inputs":items[i:i+100]}).encode(), headers=H, method='POST')
    try:
        ok += len(json.load(urllib.request.urlopen(r)).get("results", []))
    except urllib.error.HTTPError as e:
        print("  ERR", e.code, e.read().decode()[:250])
    time.sleep(0.25)
print("\nWRITTEN TO %d CONTACT RECORDS" % ok)
print()
for k, v in collections.Counter(p.get("ai__decision_maker_verdict") for p in writes.values() if p.get("ai__decision_maker_verdict")).most_common():
    print("   %-26s %d" % (k, v))
print()
for k, v in collections.Counter(p.get("ai__contact_status_flag") for p in writes.values() if p.get("ai__contact_status_flag")).most_common():
    print("   FLAG %-21s %d" % (k, v))
