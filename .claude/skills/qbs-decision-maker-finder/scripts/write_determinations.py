"""Write hand-read decision-maker determinations. CASES comes from reading, not regex."""
import json, os, sys, urllib.request, time
from resolver import resolve, candidates, H

PORTAL = "516382"
CASES = json.load(open(sys.argv[1]))
written = 0; nearmiss = []

for c in CASES:
    cands, direct = candidates(c["call"])
    if not c.get("assoc"):          # look it up rather than transcribe it by hand
        for x in cands:
            if x["id"] in direct:
                p = x["properties"]
                c["assoc"] = ("%s %s" % (p.get("firstname") or "", p.get("lastname") or "")).strip()
                break
    cid, role_state, crm_name, strength = resolve(c.get("dm"), c["call"], cands)
    in_hs = "Yes" if cid else ("No" if c.get("dm") else None)

    if c.get("dm"):
        shown = c["dm"]
        if crm_name and crm_name.lower() != c["dm"].lower():
            shown = "%s (CRM: %s)" % (c["dm"], crm_name)
        head = "%s [%s]" % (shown, c["conf"])
        if c.get("role"): head += " - " + c["role"]
        head += " - " + ("IN HUBSPOT" if cid else "NOT IN HUBSPOT")
    else:
        head = "No decision maker established [UNRESOLVED]"

    props = {
        "ai__decision_maker": ("%s - %s [source: call id %s, logged %s, logged against: %s] ** %s"
            % (head, c["ev"], c["call"], c["logged"], c.get("assoc") or "no contact", c["why"]))[:65000],
        "ai__associated_contact_is_dm": c["assoc_is_dm"],
    }
    if c.get("dm"):
        props["ai__decision_maker_name"] = crm_name or c["dm"]
        props["ai__decision_maker_in_hubspot"] = in_hs
        props["ai__decision_maker_buying_role"] = role_state
        if cid:
            props["ai__decision_maker_contact_id"] = "https://app.hubspot.com/contacts/%s/contact/%s" % (PORTAL, cid)

    r = urllib.request.Request("https://api.hubapi.com/crm/v3/objects/calls/%s" % c["call"],
                               data=json.dumps({"properties": props}).encode(), headers=H, method='PATCH')
    try:
        urllib.request.urlopen(r); written += 1
        tag = ("-> %s (%s)" % (crm_name, role_state)) if cid else ("NOT IN HUBSPOT" if c.get("dm") else "")
        print("  %-14s %-22s %s" % (c["call"], c.get("dm") or "(none)", tag))
    except urllib.error.HTTPError as e:
        print("  %-14s FAILED %s" % (c["call"], e.read().decode()[:140]))

    # a strength-1 near-miss is neither a match nor a clean gap - a human decides
    if c.get("dm") and not cid and strength == 1:
        best = None
        for x in cands:
            p = x["properties"]
            nm = ("%s %s" % (p.get("firstname") or "", p.get("lastname") or "")).strip()
            from resolver import score
            if score(c["dm"], p.get("firstname"), p.get("lastname")) == 1: best = nm; break
        nearmiss.append((c["call"], c["dm"], best))
    time.sleep(0.2)

print("\nwritten: %d" % written)
if nearmiss:
    print("\nNEAR MISSES - flagged 'NOT IN HUBSPOT' but a similar name exists. Check by hand:")
    for cl, dm, nm in nearmiss:
        print("  call %s: note says %-20s CRM has %s" % (cl, dm, nm))
