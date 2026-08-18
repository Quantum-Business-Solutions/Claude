"""Consolidate every wave-2 agent result into HubSpot in ONE pass.

Design notes that are load-bearing, learned the hard way earlier in this project:

* Batch create AND batch update are all-or-nothing in HubSpot. A single unique-value
  conflict rejects the entire batch (we lost 83 of 83 creates that way once, and 100 of
  149 updates another time). So: pre-check both unique properties LIVE, then write
  per-record with a fallback.
* `associatedcompanyid` in a CREATE payload is accepted and SILENTLY IGNORED. The
  association must be a separate v4 PUT afterwards, and must be verified through the v4
  endpoint - the derived property lags by seconds and reading it back looks like data loss.
* Setting hs_lead_status to 'Retired - Remove from All Lists' or 'No Longer with Company'
  triggers a portal workflow that BLANKS jobtitle ~20s later (proven via
  propertiesWithHistory; 8,067 contacts already affected). So the title is preserved into
  ai__contact_evidence BEFORE the status is set.
* Company object IDs shift on every merge and a stale ID returns a hollow record rather
  than an error, so company ids are re-resolved at write time.
"""
import os, sys, json, glob, re, time, urllib.request, urllib.error
from collections import Counter, defaultdict

S = '/tmp/claude-0/-home-user-Claude/adc041a4-59ce-53c7-8a85-ffe65b71c860/scratchpad'
H = {"Authorization": "Bearer " + os.environ['TOKEN'], "Content-Type": "application/json"}
DRY = '--write' not in sys.argv


def req(m, p, b=None, tries=5):
    for a in range(tries):
        try:
            r = urllib.request.Request("https://api.hubapi.com" + p,
                                       data=(json.dumps(b).encode() if b is not None else None),
                                       headers=H, method=m)
            raw = urllib.request.urlopen(r, timeout=90).read()
            return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503):
                time.sleep(2 * (a + 1)); continue
            return {'_err': e.code, '_b': e.read().decode()[:400]}
        except Exception as ex:
            time.sleep(2 * (a + 1))
            if a == tries - 1:
                return {'_err': str(ex)}
    return {'_err': 'retry-exhausted'}


FREE = set("""gmail googlemail yahoo ymail rocketmail hotmail outlook live msn aol icloud me mac
protonmail proton gmx mail zoho yandex comcast verizon att sbcglobal bellsouth cox charter spectrum
earthlink juno netzero roadrunner rr optonline frontier windstream embarqmail q shaw rogers sympatico
telus bell midco""".split())


def is_free(e):
    return bool(e) and '@' in e and e.rsplit('@', 1)[1].rsplit('.', 1)[0].lower() in FREE


def canon_li(u):
    """Exact-string unique property, so the form has to be canonical or dedup fails silently."""
    if not u:
        return None
    m = re.search(r'linkedin\.com/in/([^/?#]+)', u.strip(), re.I)
    return f"https://linkedin.com/in/{m.group(1).rstrip('/').lower()}" if m else None


DM_WORDS = ('owner', 'president', 'ceo', 'chief', 'founder', 'partner', 'principal', 'vp ',
            'vice president', 'director', 'general manager', 'coo', 'cfo', 'cto', 'cio',
            'managing', 'executive', 'svp', 'evp', 'head of', 'branch manager')


def looks_dm(t):
    t = (t or '').lower()
    return any(k in t for k in DM_WORDS)



# ---------------------------------------------------------------- the validated=Yes gate
# Shawn's standard, in his words: "if we validate them, they better have the up to date
# information and be with that company." So validated='Yes' asserts two things at once - the
# information is current AND the person is at THIS company. A row whose own evidence text admits
# otherwise cannot carry it.
#
# The gate does NOT re-derive every verdict from scratch. An earlier attempt at that over-fired
# badly: it downgraded people named as President on their own dealer's live team page, which is
# exactly the first-party currency proof the standard wants. The agents were briefed on this
# standard and demonstrably applied it, so the gate's job is narrower - catch the rows that
# betray their own uncertainty.
UNSURE = re.compile(r"(?i)\bunverified\b|\bunconfirmed\b|could not (confirm|verify|corroborate)|"
                    r"status (unverified|unconfirmed|unknown)|post-close status|not (independently )?confirmed|"
                    r"\bno post-\d|\bmay have\b|\blikely\b|\bprobabl|\bappears to\b|\bpresumably\b|"
                    r"\bassumed\b|\bunsupported\b|\bthin profile\b|\bdateless\b|\bstale\b|"
                    r"no source names|absent from|not on the .{0,24}team page|"
                    r"\bhold\b.{0,30}human|needs (a )?human|cannot be confirmed")
HISTMARK = re.compile(r"(?i)\bat time of\b|\bformer\b|\bretired\b|role ended|\bdeparted\b|"
                      r"no longer (with|at)|sold (his|her|the) (equity|business|company)|"
                      r"end:\s*\d{1,2}/\d")
DOCROLE = re.compile(r"(?i)^primary (contract )?contact|^principal contact|^contract contact|"
                     r"primary contact for")

def gate_validated(p):
    """Return (validated_value, downgrade_reason_or_None)."""
    if p.get('validated') != 'Yes':
        return (p.get('validated') or 'Needs Updated'), None
    ev = (p.get('evidence') or '') + ' ' + (p.get('note') or '')
    ti = (p.get('title') or '')
    m = UNSURE.search(ev)
    if m:
        return 'Needs Updated', f'the evidence admits the currency is not established ("{m.group(0)}")'
    if HISTMARK.search(ti):
        return 'Needs Updated', 'the title itself carries a historical marker'
    m = HISTMARK.search(ev)
    if m:
        return 'Needs Updated', f'the evidence carries a historical marker ("{m.group(0)}")'
    if DOCROLE.search(ti.strip()):
        return 'Needs Updated', ('the "title" is the role this person played in a procurement '
                                 'document, not a confirmed job title')
    return 'Yes', None

_gate_stats = Counter()

def validated_for(p):
    v, why = gate_validated(p)
    if why:
        _gate_stats['downgraded from Yes'] += 1
        p['_gate_note'] = (
            f"VALIDATION DOWNGRADED FROM 'Yes' TO 'Needs Updated' 2026-08-17. Reason: {why}. "
            f"The standard for 'Yes' on this project is that the record is CURRENT and the person "
            f"is AT THIS COMPANY - both, evidenced. This row's own evidence does not carry that, so "
            f"the find is retained with its evidence but not marked validated. It is a lead to close "
            f"out, not a confirmed contact.")
    elif v == 'Yes':
        _gate_stats['validated Yes, met the bar'] += 1
    return v

# ---------------------------------------------------------------- load agent output
records = []
for f in sorted(glob.glob(os.path.join(S, 'wave2', '*_result.json'))):
    shard = os.path.basename(f).split('_')[0]
    try:
        d = json.load(open(f))
    except Exception as ex:
        print(f'  !! {shard} unreadable: {ex}'); continue
    if not isinstance(d, list):
        print(f'  !! {shard} is not a list, skipped'); continue
    for r in d:
        r['_shard'] = shard
        records.append(r)
print(f'agent records loaded: {len(records)} from {len(set(r["_shard"] for r in records))} shards')

hold = set(json.load(open(os.path.join(S, 'xlsx_data.json')))['hold'])

# current company verdicts, so we never create a prospect at a dead or out-of-scope company
CO = {}
after = None
while True:
    b = {"filterGroups": [{"filters": [{"propertyName": "copier_company", "operator": "EQ", "value": "true"}]}],
         "properties": ["name", "domain", "ai__dealer_verdict", "ai__acquired_by"], "limit": 100}
    if after:
        b["after"] = after
    r = req('POST', "/crm/v3/objects/companies/search", b)
    for c in r.get("results", []):
        CO[c['id']] = c['properties']
    after = (r.get("paging") or {}).get("next", {}).get("after")
    if not after:
        break
print(f'dealer companies: {len(CO)}   client-hold: {len(hold)}')

EXCLUDE_VERDICT = {'non_us', 'defunct', 'not_dealer'}

# ---------------------------------------------------------------- triage every person row
create, update, suppress, depart, held = [], [], [], [], []
for r in records:
    cid = str(r.get('cid') or '')
    co = CO.get(cid, {})
    verdict = r.get('company_verdict') or co.get('ai__dealer_verdict')
    for p in (r.get('people') or []):
        p = dict(p)
        p['_cid'], p['_co'] = cid, r.get('company')
        p['_shard'] = r['_shard']
        p['linkedin_url'] = canon_li(p.get('linkedin_url'))
        eid = p.get('existing_contact_id')

        if (p.get('wrong_identity') or p.get('is_wrong_person')
                or p.get('wrong_identity_linkedin_rejected')
                or p.get('wrong_company_association')):
            suppress.append(p); continue
        if p.get('departed'):
            depart.append(p); continue
        if eid:
            update.append(p); continue

        # --- from here down these are candidate NEW contacts. The bar is deliberately high:
        # the brief is "only put in new contacts that make sense for what we are trying to
        # accomplish", i.e. reachable decision-makers at live US dealers.
        why = None
        if cid in hold:
            why = 'client account on hold - never written by design'
        elif verdict in EXCLUDE_VERDICT:
            why = f'company verdict is {verdict} - not a US dealer prospect'
        elif not (p.get('is_decision_maker') or looks_dm(p.get('title'))):
            why = 'below the decision-maker bar'
        elif p.get('validated') != 'Yes' and not p.get('email'):
            why = 'neither validated nor reachable - not enough to justify a new record'
        if why:
            p['_why'] = why; held.append(p)
        else:
            create.append(p)

print(f'\ntriage: create-candidates {len(create)} | update {len(update)} | '
      f'suppress {len(suppress)} | departures {len(depart)} | held {len(held)}')
print('held, by reason:')
for k, c in Counter(p['_why'] for p in held).most_common():
    print(f'  {c:4d}  {k}')
json.dump({'create': create, 'update': update, 'suppress': suppress,
           'depart': depart, 'held': held},
          open(os.path.join(S, 'wave2', 'triage.json'), 'w'), indent=1)


# ---------------------------------------------------------------- pre-create guards
# Three failure modes found in the dry run, each of which would have put junk in the portal.
def _nm(x):
    return ((x.get('firstname') or '').strip().lower() + ' ' +
            (x.get('lastname') or '').strip().lower()).strip()

# GUARD 1 - the same human already carries a HubSpot id somewhere else in this wave. Two agents
# working different company records found the same person (e.g. Peter Stelling appeared as an
# existing contact on Benchmark and as a "new" person on Graphic Enterprises). Creating them
# again makes the duplicate the unique properties are supposed to prevent.
known_ids = {}
for _p in update + depart:
    _e = _p.get('existing_contact_id')
    if _e:
        known_ids.setdefault(_nm(_p), (_e, _p.get('_co')))

# GUARD 2 - the person's title names the record's OWN ACQUIRER, i.e. they are the acquiring
# group's corporate executive, not staff of the dealer whose record this is. Attaching them to
# the retired brand would (a) duplicate one executive across every brand the group bought and
# (b) put people on precisely the records Shawn's retired-brand consolidation is going to merge
# away. They belong on the ACQUIRER's company record instead.
acq_by_cid = {str(r['cid']): r['acquired_by'] for r in records if r.get('acquired_by')}

def names_the_acquirer(_p):
    a = acq_by_cid.get(str(_p['_cid']))
    if not a:
        return None
    toks = [w for w in a.replace(',', ' ').replace('/', ' ').split() if len(w) > 3][:2]
    t = (_p.get('title') or '').lower()
    return a if any(w.lower() in t for w in toks) else None

kept = []
for p in create:
    if _nm(p) in known_ids:
        eid, where = known_ids[_nm(p)]
        p['existing_contact_id'] = eid
        p['_folded_from'] = f'same human already on contact {eid} via {where}'
        update.append(p)
        continue
    a = names_the_acquirer(p)
    if a:
        p['_why'] = (f'acquirer corporate executive - title names {a}, which is this record\'s '
                     f'acquirer, not the dealer. Belongs on the acquirer company record.')
        held.append(p)
        continue
    kept.append(p)
create = kept
print(f'\nguard 1 (same human elsewhere in wave 2) folded : '
      f'{sum(1 for x in update if x.get("_folded_from"))}')
print(f'guard 2 (acquirer corporate exec, wrong record) : '
      f'{sum(1 for x in held if "acquirer corporate" in (x.get("_why") or ""))}')
print(f'create candidates after guards: {len(create)}')

# GUARD 3 - a create candidate with NEITHER a LinkedIn URL nor an email has no unique key, so
# HubSpot cannot reject it as a duplicate. Check the portal by exact name at the same company
# before creating. Deliberately scoped to first+last AT THE SAME COMPANY: a looser surname
# match produced 96 false positives earlier in this project.
nokey = [p for p in create if not p.get('linkedin_url') and not p.get('email')]
print(f'guard 3: name-checking {len(nokey)} create candidates that have no unique key')
folded3 = 0
for p in nokey:
    r = req('POST', "/crm/v3/objects/contacts/search",
            {"filterGroups": [{"filters": [
                {"propertyName": "firstname", "operator": "EQ", "value": (p.get('firstname') or '')},
                {"propertyName": "lastname", "operator": "EQ", "value": (p.get('lastname') or '')},
                {"propertyName": "associatedcompanyid", "operator": "EQ", "value": p['_cid']}]}],
             "properties": ["firstname", "lastname", "jobtitle"], "limit": 3})
    hits = r.get('results', [])
    if hits:
        p['existing_contact_id'] = hits[0]['id']
        p['_folded_from'] = f'exact first+last already at this company as contact {hits[0]["id"]}'
        update.append(p)
        create.remove(p)
        folded3 += 1
print(f'guard 3 folded: {folded3}   create candidates now: {len(create)}')

# ---------------------------------------------------------------- live uniqueness pre-check
def find_by(prop, val):
    r = req('POST', "/crm/v3/objects/contacts/search",
            {"filterGroups": [{"filters": [{"propertyName": prop, "operator": "EQ", "value": val}]}],
             "properties": ["firstname", "lastname", "email", "jobtitle", "associatedcompanyid",
                            "hs_lead_status", "linkedin_profile_url__unique_value"], "limit": 5})
    return r.get('results', [])


dupe, clean = [], []
for p in create:
    hit = None
    if p.get('linkedin_url'):
        for h in find_by('linkedin_profile_url__unique_value', p['linkedin_url']):
            hit = ('linkedin_profile_url__unique_value', h); break
    if not hit and p.get('email'):
        for h in find_by('email', p['email']):
            hit = ('email', h); break
    if hit:
        p['_dupe_on'], p['_dupe_id'] = hit[0], hit[1]['id']
        p['_dupe_name'] = ((hit[1]['properties'].get('firstname') or '') + ' ' +
                           (hit[1]['properties'].get('lastname') or '')).strip()
        dupe.append(p)
    else:
        clean.append(p)
print(f'\nuniqueness pre-check: already in portal {len(dupe)} | genuinely new {len(clean)}')
json.dump({'dupe': dupe, 'clean': clean},
          open(os.path.join(S, 'wave2', 'uniq.json'), 'w'), indent=1)


# ---------------------------------------------------------------- review exports
import csv
allp = create + update + dupe + suppress + depart + held
with open(os.path.join(S, 'INFERRED_EMAILS_TO_VERIFY.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['company', 'contact_id', 'first', 'last', 'title', 'inferred_email',
                'pattern_anchor_and_evidence', 'shard'])
    n = 0
    for p_ in allp:
        if p_.get('email') and p_.get('email_confidence') == 'inferred':
            w.writerow([p_.get('_co'), p_.get('existing_contact_id') or p_.get('_dupe_id') or '',
                        p_.get('firstname'), p_.get('lastname'), p_.get('title'), p_['email'],
                        (p_.get('evidence') or '')[:600], p_.get('_shard')])
            n += 1
print(f'\nINFERRED_EMAILS_TO_VERIFY.csv: {n} pattern-guessed addresses held OUT of the business '
      f'email field, staged for a verification run before any of them is trusted.')

with open(os.path.join(S, 'WAVE2_NEEDS_HUMAN.csv'), 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['company', 'contact_id', 'first', 'last', 'title', 'email', 'validated',
                'flag', 'evidence', 'shard'])
    n = 0
    for p_ in allp:
        flags = [k for k in ('needs_human', 'wrong_identity', 'wrong_company_association',
                             'duplicate_of', 'departed', 'wrong_identity_linkedin_rejected')
                 if p_.get(k)]
        if not flags:
            continue
        w.writerow([p_.get('_co'), p_.get('existing_contact_id') or p_.get('_dupe_id') or '',
                    p_.get('firstname'), p_.get('lastname'), p_.get('title'), p_.get('email'),
                    p_.get('validated'), ';'.join(flags), (p_.get('evidence') or '')[:800],
                    p_.get('_shard')])
        n += 1
print(f'WAVE2_NEEDS_HUMAN.csv: {n} rows flagged for a human call.')

if DRY:
    print('\nDRY RUN - nothing written. Re-run with --write to apply.')
    sys.exit(0)

# ---------------------------------------------------------------- writes
def route_email(p):
    """Shawn's rule: business + no existing email -> email; business + existing -> email_other;
    personal -> linkedin__email ONLY, never the business field; unknown -> held for review."""
    e, cls = p.get('email'), (p.get('email_class') or '')
    props = {}
    if not e:
        return props
    props['linkedin__email'] = e                       # provenance, always
    if cls == 'personal' or is_free(e):
        return props
    if cls == 'unknown':
        return props
    if p.get('email_confidence') == 'inferred':
        return props                                   # a guess never occupies the business field
    props['email'] = e
    return props


def evidence(p, extra=''):
    bits = [f"WAVE 2 SWEEP 2026-08-17 (shard {p.get('_shard')}) - {p.get('_co')}."]
    if p.get('evidence'):
        bits.append(str(p['evidence']))
    if p.get('email') and p.get('email_confidence') == 'inferred':
        bits.append(f"EMAIL {p['email']} IS PATTERN-INFERRED, NOT VERIFIED - held out of the "
                    f"business email field and recorded here only.")
    if p.get('_gate_note'):
        bits.append(p['_gate_note'])
    if p.get('_folded_from'):
        bits.append(f"DEDUP: {p['_folded_from']}.")
    if extra:
        bits.append(extra)
    return '\n\n'.join(bits)[:65000]


def associate(pid, cid):
    r = req('PUT', f"/crm/v4/objects/contacts/{pid}/associations/companies/{cid}",
            [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 1}])
    chk = req('GET', f"/crm/v4/objects/contacts/{pid}/associations/companies")
    return any(str(x.get('toObjectId')) == str(cid) for x in chk.get('results', []))


stats = Counter()

for p in clean:
    props = {
        "firstname": p.get('firstname'), "lastname": p.get('lastname'),
        "jobtitle": p.get('title'),
        "validated__linkedin_or_manually": validated_for(p),
        "ai__contact_evidence": evidence(p),
        "hs_lead_status": "ConnectandSell Prospect",
    }
    if p.get('linkedin_url'):
        props["linkedin_profile_url__unique_value"] = p['linkedin_url']
    if p.get('phone'):
        props["phone"] = p['phone']
    props.update(route_email(p))
    props = {k: v for k, v in props.items() if v}
    r = req('POST', "/crm/v3/objects/contacts", {"properties": props})
    if '_err' in r:
        # a conflict here means the pre-check raced; retry without the colliding unique field
        props.pop('email', None); props.pop('linkedin_profile_url__unique_value', None)
        r = req('POST', "/crm/v3/objects/contacts", {"properties": props})
        if '_err' in r:
            stats['create FAILED'] += 1
            print('  create failed:', p.get('firstname'), p.get('lastname'), r.get('_err'))
            continue
        stats['created without a unique field (conflict)'] += 1
    else:
        stats['created'] += 1
    if associate(r['id'], p['_cid']):
        stats['associated to company'] += 1
    else:
        stats['ASSOCIATION FAILED'] += 1
        print('  association failed:', r['id'], p['_cid'])

for p in update + dupe:
    pid = p.get('existing_contact_id') or p.get('_dupe_id')
    if not pid:
        continue
    cur = req('GET', f"/crm/v3/objects/contacts/{pid}"
                     "?properties=email,jobtitle,ai__contact_evidence,hs_lead_status")
    cp = cur.get('properties', {}) or {}
    _v = validated_for(p) if p.get('validated') else None
    props = {"ai__contact_evidence": ((cp.get('ai__contact_evidence') or '') + '\n\n' +
                                      evidence(p))[:65000]}
    if _v:
        props["validated__linkedin_or_manually"] = _v
    if p.get('title') and p['title'] != cp.get('jobtitle'):
        props["jobtitle"] = p['title']
        stats['title corrected'] += 1
    if p.get('linkedin_url'):
        props["linkedin_profile_url__unique_value"] = p['linkedin_url']
    em = route_email(p)
    if em.get('email'):
        if cp.get('email'):
            if cp['email'].lower() != em['email'].lower():
                props['email_other'] = em['email']       # never overwrite a live business email
                stats['second email -> email_other'] += 1
        else:
            props['email'] = em['email']
            stats['business email filled'] += 1
    if em.get('linkedin__email'):
        props['linkedin__email'] = em['linkedin__email']
    r = req('PATCH', f"/crm/v3/objects/contacts/{pid}", {"properties": props})
    if '_err' in r:
        props.pop('email', None); props.pop('linkedin_profile_url__unique_value', None)
        r = req('PATCH', f"/crm/v3/objects/contacts/{pid}", {"properties": props})
        stats['updated after dropping a conflicting unique field' if '_err' not in r
              else 'update FAILED'] += 1
    else:
        stats['updated'] += 1

for p in suppress:
    pid = p.get('existing_contact_id')
    if not pid:
        continue
    cur = req('GET', f"/crm/v3/objects/contacts/{pid}?properties=ai__contact_evidence,jobtitle")
    cp = cur.get('properties', {}) or {}
    ev = (f"WRONG IDENTITY ON THE LINKEDIN FIELD - wave 2, {p.get('_co')}. {p.get('evidence')}\n\n"
          f"The linkedin_profile_url__unique_value has been CLEARED because that property is a "
          f"unique key: while it holds another human's URL it blocks the real person at this dealer "
          f"from ever being created. TITLE AT SUPPRESSION: {cp.get('jobtitle') or '(none)'}. "
          f"Deletion is NOT being performed here - that is a human call.")
    r = req('PATCH', f"/crm/v3/objects/contacts/{pid}",
            {"properties": {"linkedin_profile_url__unique_value": "",
                            "hs_lead_status": "Incorrect Contact",
                            "validated__linkedin_or_manually": "Needs Updated",
                            "ai__contact_evidence": ((cp.get('ai__contact_evidence') or '') +
                                                     '\n\n' + ev)[:65000]}})
    stats['suppressed wrong identity' if '_err' not in r else 'suppress FAILED'] += 1

for p in depart:
    pid = p.get('existing_contact_id')
    if not pid:
        continue
    cur = req('GET', f"/crm/v3/objects/contacts/{pid}?properties=ai__contact_evidence,jobtitle")
    cp = cur.get('properties', {}) or {}
    # title first: the status write triggers a workflow that blanks jobtitle ~20s later
    ev = (f"DEPARTURE CONFIRMED - wave 2, {p.get('_co')}. {p.get('evidence')}\n\n"
          f"TITLE AT DEPARTURE: {cp.get('jobtitle') or p.get('title') or '(none)'}. "
          f"Recorded here because a portal workflow blanks the jobtitle field within about twenty "
          f"seconds of this lead status being set - 8,067 contacts have already lost their title "
          f"that way, so the title is preserved in this note before the status is written.")
    req('PATCH', f"/crm/v3/objects/contacts/{pid}",
        {"properties": {"ai__contact_evidence": ((cp.get('ai__contact_evidence') or '') +
                                                 '\n\n' + ev)[:65000]}})
    r = req('PATCH', f"/crm/v3/objects/contacts/{pid}",
            {"properties": {"hs_lead_status": "No Longer with Company",
                            "validated__linkedin_or_manually": "Needs Updated"}})
    stats['departure recorded' if '_err' not in r else 'departure FAILED'] += 1

# ---------------------------------------------------------------- company-level writes
for r0 in records:
    cid = str(r0.get('cid') or '')
    if cid not in CO or cid in hold:
        continue
    props = {}
    v = r0.get('company_verdict')
    if v in ('dealer', 'dealer_bad_domain', 'not_dealer', 'acquired', 'defunct', 'non_us', 'unresolved'):
        props['ai__dealer_verdict'] = v
    if r0.get('acquired_by'):
        props['ai__acquired_by'] = r0['acquired_by']
        props['ai__acquisition_status'] = 'Confirmed Acquired'
    if r0.get('company_notes'):
        cur = req('GET', f"/crm/v3/objects/companies/{cid}?properties=ai__data_quality_notes")
        prev = (cur.get('properties', {}) or {}).get('ai__data_quality_notes') or ''
        stamp = (f"\n\nWAVE 2 SWEEP 2026-08-17 (shard {r0['_shard']}) - outcome: "
                 f"{r0.get('outcome')}. {r0['company_notes']}")
        if r0.get('domain_correction'):
            stamp += (f" DOMAIN CORRECTION SUGGESTED: {r0['domain_correction']} - recorded here rather "
                      f"than written over the domain field, because overwriting a company domain has "
                      f"knock-on effects on dedup and on the acquired-brand design.")
        if r0.get('sources_tried'):
            st = r0['sources_tried']
            st = st if isinstance(st, list) else [st]
            stamp += " SOURCES TRIED: " + ', '.join(str(x) for x in st) + '.'
        props['ai__data_quality_notes'] = (prev + stamp)[:65000]
    if not props:
        continue
    rr = req('PATCH', f"/crm/v3/objects/companies/{cid}", {"properties": props})
    stats['company updated' if '_err' not in rr else 'company update FAILED'] += 1

print('\n=== validated=Yes gate ===')
for k, c in _gate_stats.most_common():
    print(f'  {c:5d}  {k}')

print('\n=== write results ===')
for k, c in stats.most_common():
    print(f'  {c:5d}  {k}')
json.dump(dict(stats), open(os.path.join(S, 'wave2', 'write_stats.json'), 'w'), indent=1)
