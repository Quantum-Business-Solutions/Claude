"""Contact resolution for decision-maker writes.

Exact matching manufactures false gaps. Measured misses from live UBEO data:
  note "Amy Greenlee"     -> contact "Amy Greenlee Holland"  (containment)
  note "Britney Hurlbert" -> contact "Brittany Hurlburt"     (spelling)
  note "Eric Porter"      -> contact "Erik Porter"           (spelling)
  note "Krista Gallio"    -> contact "Christa Galleo"        (phonetic)
Search DIRECTLY ASSOCIATED contacts first, then the company roster - a call
with a contact but no company must not report NoContact.
"""
import json, os, re, time, urllib.request, difflib

H = {'Authorization': 'Bearer ' + os.environ['PAT'], 'Content-Type': 'application/json'}

def post(u, b):
    for i in range(5):
        try:
            r = urllib.request.Request(u, data=json.dumps(b).encode(), headers=H, method='POST')
            return json.load(urllib.request.urlopen(r))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503,504): time.sleep(2*(i+1)); continue
            return {}
        except Exception: time.sleep(2*(i+1))
    return {}

def norm(s): return re.sub(r"[^a-z]", "", (s or "").lower())

def lev(a, b):
    if abs(len(a)-len(b)) > 3: return 99
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j]+1, cur[j-1]+1, prev[j-1]+(ca != cb)))
        prev = cur
    return prev[-1]

PHON = [("ph","f"),("ch","k"),("ck","k"),("sch","sk"),("c","k"),("z","s"),("y","i"),("ee","i")]
def phon(x):
    x = norm(x)
    for a, b in PHON: x = x.replace(a, b)
    out = []
    for ch in x:
        if not out or out[-1] != ch: out.append(ch)   # collapse doubles
    return "".join(out)

def _pref(a, b):
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]: n += 1
    return n

def score(want, cand_first, cand_last):
    """0 no match | 1 weak, needs a human | 2 fuzzy, eyeball it | 3 confident.

    Only >=2 is written. The bar is deliberately high on FIRST names: at one
    edit apart sit Eric/Erik (same person) and Mark/Mary, Kim/Tim (different
    people), so edit distance alone cannot decide and phonetics must.
    """
    w = norm(want); cf = norm(cand_first); cl = norm(cand_last); full = cf + cl
    if not w or not full: return 0
    if w == full: return 3
    if w in full or full in w: return 3                        # Amy Greenlee / Greenlee Holland
    parts = [p for p in re.split(r"\s+", want.strip()) if p]
    if len(parts) < 2:
        wf = norm(parts[0])
        if len(wf) > 3 and wf == cf: return 2                  # lone distinctive first name
        return 1 if (len(wf) > 3 and phon(wf) == phon(cf)) else 0
    wf, wl = norm(parts[0]), norm(parts[-1])
    if not wl or not cl: return 0
    dl, df = lev(wl, cl), lev(wf, cf)
    long_pair = len(wf) >= 6 and len(cf) >= 6
    fn_same = (wf == cf
               or (min(len(wf), len(cf)) >= 3 and (wf in cf or cf in wf))   # Jon / Jonathan
               or phon(wf) == phon(cf))                                     # Eric / Erik
    # a surname whose FIRST letter differs is a different family, not a typo:
    # Wright/Bright, Green/Breen. Cusimano/Cucumano and Gallio/Galleo differ inside.
    same_ln_initial = wl[0] == cl[0]
    if dl == 0:
        if fn_same: return 3
        if long_pair and _pref(wf, cf) >= 4: return 1          # Britney/Brittany AND Michael/Michelle -> human
        if long_pair and df <= 2 and _pref(wf, cf) >= 3: return 2   # Steven/Stephen, Sabina/Sabrina
        return 1                                               # Mark/Mary, Kim/Tim -> human
    if dl == 1 and same_ln_initial:
        if fn_same: return 3                                   # Grace Cusimano / Cucumano
        if long_pair and df <= 2: return 2
        if long_pair and _pref(wf, cf) >= 4: return 1
        return 1
    if dl == 1: return 1                                       # Wright / Bright -> human
    if dl == 2 and fn_same and same_ln_initial and len(wl) >= 7: return 2
    if difflib.SequenceMatcher(None, w, full).ratio() >= 0.90: return 2
    return 0

def candidates(call_id):
    """directly-associated contacts first, then everyone at the company"""
    out, seen = [], set()
    d = post("https://api.hubapi.com/crm/v4/associations/calls/contacts/batch/read", {"inputs":[{"id":call_id}]})
    direct = [str(t["toObjectId"]) for r in d.get("results",[]) for t in r.get("to",[])]
    d = post("https://api.hubapi.com/crm/v4/associations/calls/companies/batch/read", {"inputs":[{"id":call_id}]})
    comps = [str(t["toObjectId"]) for r in d.get("results",[]) for t in r.get("to",[])]
    roster = []
    if comps:
        d2 = post("https://api.hubapi.com/crm/v4/associations/companies/contacts/batch/read", {"inputs":[{"id":comps[0]}]})
        roster = [str(t["toObjectId"]) for r in d2.get("results",[]) for t in r.get("to",[])]
    ids = [c for c in direct + roster if not (c in seen or seen.add(c))]
    if not ids: return [], direct
    for i in range(0, min(len(ids), 200), 100):
        d3 = post("https://api.hubapi.com/crm/v3/objects/contacts/batch/read",
                  {"properties":["firstname","lastname","hs_buying_role","jobtitle"],
                   "inputs":[{"id":c} for c in ids[i:i+100]]})
        for r in d3.get("results", []): out.append(r)
    order = {c: n for n, c in enumerate(ids)}
    out.sort(key=lambda r: order.get(r["id"], 999))
    return out, direct

def resolve(name, call_id, cands=None):
    """-> (contact_id, buying_role_state, matched_name, match_strength)"""
    if not name: return None, "NoContact", None, 0
    if cands is None: cands, _ = candidates(call_id)
    best = (0, None)
    for r in cands:
        p = r["properties"]
        s = score(name, p.get("firstname"), p.get("lastname"))
        if s > best[0]: best = (s, r)
        if s == 3: break
    if best[0] < 2: return None, "NoContact", None, best[0]
    p = best[1]["properties"]
    br = p.get("hs_buying_role") or ""
    state = "AlreadySet" if "DECISION_MAKER" in br else ("OtherRole" if br else "NotSet")
    nm = ("%s %s" % (p.get("firstname") or "", p.get("lastname") or "")).strip()
    return best[1]["id"], state, nm, best[0]
