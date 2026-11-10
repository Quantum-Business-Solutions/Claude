"""Why aren't we booking more meetings? Builds a ClientCommand page from scored call records.

    python3 meetings_analysis.py --since 2026-09-28 [--create | --update <proposalId>]

Reads calls with a CAS transcript since the date (HubSpot), computes the funnel per rep and the patterns behind it,
and renders one self-contained HTML page. Totals, percentages and short rep-side quotes only - no prospect names.
"""
import os, sys, json, re, html, datetime, collections, random, statistics as st
from clients import hs

P = 'cas_coach_'
PROPS = ['hs_timestamp', 'hubspot_owner_id', 'hs_call_duration', 'cas_transcript'] + [P + k for k in (
    'stage_reached', 'opener', 'ask_stage', 'asked_for_meeting', 'alternative_close', 'assumptive_close', 'objections',
    'objection_handling', 'prospect_interest', 'decision_maker', 'invite_confirmed', 'got_to_pitch', 'rep_talk_pct', 'discovery_questions', 'next_step_set', 'ask_position_pct')] + [
    'ai__signal_hubspot_status', 'ai__signal_crm_name', 'ai__signal_budget_status', 'ai__signal_outsources_appt_setting', 'ai__signal_outsources_marketing']
BOOKED = ('s10', 's11', 's12')


def load(since, until=None):
    own = {o['id']: (o.get('firstName', '') + ' ' + o.get('lastName', '')).strip() for o in hs('GET', '/crm/v3/owners?limit=500')['results']}
    rows, w = [], datetime.datetime.fromisoformat(since)
    end = (datetime.datetime.fromisoformat(until) + datetime.timedelta(days=1)) if until else datetime.datetime.utcnow() + datetime.timedelta(days=2)
    while w < end:
        w2, after = w + datetime.timedelta(days=7), 0
        while True:
            r = hs('POST', '/crm/v3/objects/calls/search', {'filterGroups': [{'filters': [
                {'propertyName': 'cas_transcript', 'operator': 'HAS_PROPERTY'},
                {'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': str(int(w.timestamp() * 1000))},
                {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': str(int(w2.timestamp() * 1000))}]}],
                'limit': 100, 'after': after, 'properties': PROPS})
            rows += r['results']; nx = (r.get('paging') or {}).get('next', {}).get('after')
            if not nx: break
            after = nx
        w = w2
    out = []
    for x in rows:
        p = x['properties']
        if not p.get(P + 'stage_reached'): continue
        p['id'] = x['id']; p['rep'] = own.get(p.get('hubspot_owner_id'), 'Other'); p['txt'] = re.sub(r'\s+', ' ', p.get('cas_transcript') or ''); out.append(p)
    return out


g = lambda p, k: p.get(P + k)
stg = lambda p: g(p, 'stage_reached')[:3]
booked = lambda p: stg(p) in BOOKED
close = lambda p: g(p, 'alternative_close') == 'yes' or g(p, 'assumptive_close') == 'yes'
pc = lambda n, d: round(100 * n / d, 1) if d else 0.0


def funnel(R):
    n = len(R); live = [p for p in R if stg(p) not in ('s01', 's02')]
    passed = [p for p in live if stg(p) not in ('s03', 's04')]
    return [('Calls with a transcript', n), ('Reached a person (not voicemail/gatekeeper)', len(live)), ('Got past the opener', len(passed)),
            ('Heard the pitch', sum(g(p, 'got_to_pitch') == 'yes' for p in R)), ('Meeting asked for', sum(g(p, 'asked_for_meeting') == 'yes' for p in R)),
            ('Meeting booked', sum(booked(p) for p in R)), ('Invite confirmed', sum(g(p, 'invite_confirmed') == 'yes' for p in R))]


def metrics(D):
    M = {}
    for rep in ('Kenzie Braun', 'Patrick Dodge'):
        R = [p for p in D if p['rep'] == rep]; n = len(R)
        asks = [p for p in R if g(p, 'asked_for_meeting') == 'yes']
        ob = [p for p in R if g(p, 'objection_handling') in ('not_handled', 'partial', 'handled_well')]
        dur = [int(p['hs_call_duration']) / 1000 for p in R if p.get('hs_call_duration')]
        M[rep] = dict(n=n, funnel=funnel(R), hung=sum(stg(p) == 's03' for p in R), refused=sum(stg(p) == 's04' for p in R),
                      live=sum(stg(p) not in ('s01', 's02') for p in R), asks=len(asks), never=sum(g(p, 'ask_stage') == 'a6_never_asked' for p in R),
                      asks_close=sum(close(p) for p in asks), asks_plain=sum(not close(p) for p in asks),
                      booked_close=sum(booked(p) and close(p) for p in R), booked_plain=sum(booked(p) and not close(p) for p in R),
                      ob=len(ob), ob_not=sum(g(p, 'objection_handling') == 'not_handled' for p in ob), ob_good=sum(g(p, 'objection_handling') == 'handled_well' for p in ob),
                      dur=round(st.median(dur)) if dur else 0, talk=(round(st.median([float(g(p, 'rep_talk_pct')) for p in R if g(p, 'rep_talk_pct')])) if any(g(p, 'rep_talk_pct') for p in R) else 0),
                      opener=collections.Counter(g(p, 'opener') for p in R), dm=collections.Counter(g(p, 'decision_maker') for p in R),
                      objs=collections.Counter(o for p in R for o in (g(p, 'objections') or '').split(';') if o and o != 'none'))
        wk = collections.defaultdict(lambda: [0, 0, 0])
        for p in R:
            d = datetime.date.fromisoformat(p['hs_timestamp'][:10]); k = (d - datetime.timedelta(days=d.weekday())).isoformat()
            wk[k][0] += 1; wk[k][1] += stg(p) not in ('s01', 's02'); wk[k][2] += booked(p)
        M[rep]['weeks'] = sorted(wk.items())
    K = [p for p in D if p['rep'] == 'Kenzie Braun']
    inter = [p for p in K if re.search(r"out of the blue|an interruption", p['txt'][:900].lower())]; rest = [p for p in K if p not in inter]
    S = [p for p in D]
    M['stage'] = {r: {k: sum(stg(p) == k for p in D if p['rep'] == r) for k, _ in STAGES} for r in ('Kenzie Braun seat', 'Patrick Dodge')} if False else None
    M['stage'] = {}
    for rep, key in (('Kenzie Braun', 'Kenzie Braun seat'), ('Patrick Dodge', 'Patrick Dodge')):
        R = [p for p in D if p['rep'] == rep]; M['stage'][key] = [pc(sum(stg(p) == k for p in R), len(R)) for k, _ in STAGES]
    nobj = lambda p: len([o for o in (g(p, 'objections') or '').split(';') if o and o != 'none'])
    M['objcount'] = {rep: collections.Counter(min(nobj(p), 3) for p in D if p['rep'] == rep) for rep in ('Kenzie Braun', 'Patrick Dodge')}
    M['allfunnel'] = funnel(D)
    M['next'] = {r: pc(sum(g(p, 'next_step_set') in ('meeting', 'callback') for p in D if p['rep'] == r), sum(1 for p in D if p['rep'] == r)) for r in ('Kenzie Braun', 'Patrick Dodge')}
    ap = lambda r: [float(g(p, 'ask_position_pct')) for p in D if p['rep'] == r and g(p, 'ask_position_pct')]
    M['askpos'] = {r: (round(st.median(ap(r))) if ap(r) else 0) for r in ('Kenzie Braun', 'Patrick Dodge')}
    M['dm_yes'] = sum(g(p, 'decision_maker') == 'yes' for p in D)
    M['notdm'] = sum('not_decision_maker' in (g(p, 'objections') or '') for p in D)
    M['pitch'] = {r: pc(sum(g(p, 'got_to_pitch') == 'yes' for p in D if p['rep'] == r), sum(1 for p in D if p['rep'] == r)) for r in ('Kenzie Braun', 'Patrick Dodge')}
    rs = random.Random(7)
    M['listen'] = dict(hang=[p['id'] for p in (lambda L_: rs.sample(L_, min(8, len(L_))))([p for p in D if p['rep'] == 'Kenzie Braun' and stg(p) == 's03'])],
                       missed=[p['id'] for p in (lambda L_: rs.sample(L_, min(8, len(L_))))([p for p in D if p['rep'] == 'Kenzie Braun' and g(p, 'got_to_pitch') == 'yes' and g(p, 'asked_for_meeting') != 'yes' and g(p, 'prospect_interest') in ('neutral', 'warm')])],
                       booked=[p['id'] for p in D if booked(p)][:8])
    sg = lambda k: collections.Counter((p.get('ai__signal_' + k) or 'not asked / unclear').lower() for p in D)
    M['sig'] = {k: sg(k) for k in ('hubspot_status', 'crm_name', 'budget_status', 'outsources_appt_setting', 'outsources_marketing')}
    M['interest'] = collections.Counter(g(p, 'prospect_interest') for p in D)
    M['interrupt'] = dict(a=len(inter), a_hang=pc(sum(stg(p) == 's03' for p in inter), len(inter)), b=len(rest), b_hang=pc(sum(stg(p) == 's03' for p in rest), len(rest)))
    M['total'] = dict(n=len(D), booked=sum(booked(p) for p in D), confirmed=sum(g(p, 'invite_confirmed') == 'yes' for p in D if booked(p)))
    return M


WARM = re.compile(r'follow[- ]?up|all time meetings|hot list|no-shows|meetings|client', re.I)


def cas_convs(since, until=None):
    from cas_sync import conversations
    a = datetime.date.fromisoformat(since); b = datetime.date.fromisoformat(until) if until else datetime.date.today(); out = {}
    while a <= b:
        e_ = min(a + datetime.timedelta(days=80), b)
        for x in conversations(str(a), str(e_)): out[x['LeadtransitId']] = x
        a = e_ + datetime.timedelta(days=1)
    return list(out.values())


def cas_metrics(since, until=None):
    cv = cas_convs(since, until)
    ms = lambda x: x['Disposition'] == 'Meeting scheduled'
    tag = lambda x: 'warm' if WARM.search(x['ListName'] + ' ' + x['OriginListName']) else 'cold'
    tb = lambda s: '10 seconds or less' if s <= 10 else '11 to 20 seconds' if s <= 20 else '21 to 40 seconds' if s <= 40 else '41 to 90 seconds' if s <= 90 else 'Over 90 seconds'
    order = ['10 seconds or less', '11 to 20 seconds', '21 to 40 seconds', '41 to 90 seconds', 'Over 90 seconds']
    C = {'n': len(cv), 'meet': sum(map(ms, cv)), 'disp': collections.Counter(x['Disposition'] for x in cv)}
    for key, f in (('seat', lambda x: 'Patrick Dodge' if x['UserName'].startswith('Patrick') else 'Kenzie Braun seat'), ('temp', tag), ('talk', lambda x: tb(float(x['TalkTime'] or 0)))):
        g_ = collections.defaultdict(list)
        for x in cv: g_[f(x)].append(x)
        C[key] = {k: (len(v), sum(map(ms, v))) for k, v in g_.items()}
    st_ = collections.defaultdict(list)
    for x in cv: st_[('Patrick Dodge' if x['UserName'].startswith('Patrick') else 'Kenzie Braun seat', tag(x))].append(x)
    C['seat_temp'] = {k: (len(v), sum(map(ms, v))) for k, v in st_.items()}
    wkc = collections.defaultdict(lambda: [0, 0])
    for x in cv:
        d_ = datetime.date.fromisoformat(x['ConversationDate'][:10]); k_ = (d_ - datetime.timedelta(days=d_.weekday())).strftime('%b %-d')
        wkc[k_][0] += 1; wkc[k_][1] += ms(x)
    C['weeks'] = list(sorted(wkc.items(), key=lambda kv: datetime.datetime.strptime(kv[0] + ' 2026', '%b %d %Y')))
    C['nopitch'] = {k: pc(sum(x['Status'].startswith('No Pitch') for x in cv if (x['UserName'].startswith('Patrick')) == (k == 'Patrick Dodge')), sum(1 for x in cv if (x['UserName'].startswith('Patrick')) == (k == 'Patrick Dodge'))) for k in ('Kenzie Braun seat', 'Patrick Dodge')}
    C['nopitch_all'] = pc(sum(x['Status'].startswith('No Pitch') for x in cv), len(cv))
    C['retired'] = sum(x['Disposition'].startswith(('Retired', 'No Longer')) for x in cv)
    C['followup'] = pc(sum(x['Status'] == 'Follow-Up' for x in cv), len(cv))
    def slot(x):
        n = re.sub(r'\D', '', x.get('ActualConnectedNumber') or '')[-10:]
        for k_, nm in (('PrimaryPhoneNumber', 'Primary'), ('SecondaryPhoneNumber', 'Secondary'), ('TertiaryPhoneNumber', 'Tertiary')):
            if n and re.sub(r'\D', '', x.get(k_) or '')[-10:] == n: return nm
        return 'Other or unknown'
    sl = collections.defaultdict(list)
    for x in cv: sl[slot(x)].append(x)
    C['slot'] = [(k, len(sl[k]), pc(sum(x['Status'].startswith('No Pitch') for x in sl[k]), len(sl[k])), sum(map(ms, sl[k]))) for k in ('Primary', 'Secondary', 'Tertiary', 'Other or unknown') if k in sl]
    for k_ in order: C['talk'].setdefault(k_, (0, 0))
    for k_ in ('warm', 'cold'): C['temp'].setdefault(k_, (0, 0))
    for k_ in ('Kenzie Braun seat', 'Patrick Dodge'): C['seat'].setdefault(k_, (0, 0))
    for s_ in ('Kenzie Braun seat', 'Patrick Dodge'):
        for tmp in ('warm', 'cold'): C['seat_temp'].setdefault((s_, tmp), (0, 0))
    C['talk_order'] = order
    own_ = {(o.get('firstName', '') + ' ' + o.get('lastName', '')).strip(): o['id'] for o in hs('GET', '/crm/v3/owners?limit=500')['results']}
    t0 = datetime.datetime.fromisoformat(since); t1 = (datetime.datetime.fromisoformat(until) + datetime.timedelta(days=1)) if until else datetime.datetime.utcnow() + datetime.timedelta(days=2)
    def dials(owner):
        r = hs('POST', '/crm/v3/objects/calls/search', {'filterGroups': [{'filters': [{'propertyName': 'hubspot_owner_id', 'operator': 'EQ', 'value': str(own_.get(owner, '0'))},
              {'propertyName': 'hs_object_source_detail_1', 'operator': 'EQ', 'value': 'ConnectAndSell'},
              {'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': str(int(t0.timestamp() * 1000))}, {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': str(int(t1.timestamp() * 1000))}]}], 'limit': 1})
        return r['total']
    NOT_CONV = ('Quick Hang up', 'Blocked By Gatekeeper', 'Voicemail Pick-up')
    C['audit'] = {}
    for seat, owner in (('Kenzie Braun seat', 'Kenzie Braun'), ('Patrick Dodge', 'Patrick Dodge')):
        R = [x for x in cv if (x['UserName'].startswith('Patrick')) == (seat == 'Patrick Dodge')]
        C['audit'][seat] = dict(dials=dials(owner), transfers=len(R), convs=sum(x['Disposition'] not in NOT_CONV for x in R), meetings=sum(map(ms, R)),
                                qh=sum(x['Disposition'] == 'Quick Hang up' for x in R), nop=sum(x['Disposition'] == 'No Pitch' for x in R),
                                dnc=sum(x['Disposition'] == 'Do Not Call' for x in R), dq=sum(x['Disposition'].startswith('Disqualified') for x in R))
    L = collections.defaultdict(list)
    for x in cv: L[x['ListName']].append(x)
    C['lists'] = sorted(((k, len(v), sum(map(ms, v))) for k, v in L.items()), key=lambda r: -r[1])[:10]
    ids = sorted({str(x['CrmId']) for x in cv if x.get('CrmId')}); by = {}
    for i in range(0, len(ids), 100):
        for r in hs('POST', '/crm/v4/associations/contacts/calls/batch/read', {'inputs': [{'id': c} for c in ids[i:i + 100]]})['results']:
            by[r['from']['id']] = [str(q['toObjectId']) for q in r['to']]
    allc = sorted({c for v in by.values() for c in v}); ts = {}
    for i in range(0, len(allc), 100):
        for r in hs('POST', '/crm/v3/objects/calls/batch/read', {'inputs': [{'id': c} for c in allc[i:i + 100]], 'properties': ['hs_timestamp']})['results']:
            ts[r['id']] = (r['properties'].get('hs_timestamp') or '')[:10]
    prior = lambda x: sum(1 for k in by.get(str(x['CrmId']), []) if ts.get(k, '9') < x['ConversationDate'][:10])
    pr_ = [prior(x) for x in cv]
    cv_s = sorted(cv, key=lambda x: x['ConversationDate']); seen = collections.Counter(); first, again = [], []
    for x in cv_s:
        c = str(x['CrmId']); (first if seen[c] == 0 else again).append(x); seen[c] += 1
    hang = lambda x: x['Disposition'] == 'Quick Hang up'; nop = lambda x: x['Disposition'] == 'No Pitch'
    st_f = lambda L: dict(n=len(L), hang=pc(sum(map(hang, L)), len(L)), nop=pc(sum(map(nop, L)), len(L)), meet=sum(map(ms, L)), rate=pc(sum(map(ms, L)), len(L)),
                          talk=round(st.median(float(x['TalkTime'] or 0) for x in L)) if L else 0)
    C['people'] = len(seen); C['multi'] = sum(1 for v in seen.values() if v >= 2); C['first'] = st_f(first); C['again'] = st_f(again)
    C['prior_med'] = {s_: round(st.median([p_ for p_, x in zip(pr_, cv) if (x['UserName'].startswith('Patrick')) == (s_ == 'Patrick Dodge')] or [0])) for s_ in ('Patrick Dodge', 'Kenzie Braun seat')}
    C['prior25'] = pc(sum(p_ >= 25 for p_ in pr_), len(pr_))
    dnc = [x for x in cv if x['Disposition'] == 'Do Not Call']
    C['dnc'] = (len(dnc), sum(1 for x in dnc if any(ts.get(k, '') > x['ConversationDate'][:10] for k in by.get(str(x['CrmId']), []))))
    km = [x for x in cv if x['UserName'].startswith('Mack')]
    C['k_cold'] = (sum(tag(x) == 'cold' for x in km), len(km))
    return C


OBJ = {'not_interested': 'Not interested', 'no_time': 'No time', 'call_back_later': 'Call back later', 'not_decision_maker': 'Not the decision maker',
       'already_have_vendor': 'Already have a vendor', 'send_info': 'Send info', 'take_me_off_list': 'Take me off the list', 'no_budget': 'No budget', 'other': 'Other'}
e = html.escape


def bars(pairs, total, color='var(--accent)'):
    return ''.join('<div class="br"><span>%s</span><span class="tr"><span class="fl" style="width:%.1f%%;background:%s"></span></span><span class="nm">%d &middot; %.1f%%</span></div>'
                   % (e(l), 100 * n / total if total else 0, color, n, 100 * n / total if total else 0) for l, n in pairs)


def funnel_table(M):
    rows = []
    for i, (lab, _) in enumerate(M['Kenzie Braun']['funnel']):
        a, b = M['Kenzie Braun']['funnel'][i][1], M['Patrick Dodge']['funnel'][i][1]
        na, nb = M['Kenzie Braun']['funnel'][0][1], M['Patrick Dodge']['funnel'][0][1]
        rows.append('<tr><td>%s</td><td class="n">%d <i>%.1f%%</i></td><td class="n">%d <i>%.1f%%</i></td></tr>' % (e(lab), a, pc(a, na), b, pc(b, nb)))
    return '<table><tr><th>Step</th><th>Kenzie Braun seat</th><th>Patrick Dodge</th></tr>%s</table>' % ''.join(rows)



STAGES = [('s01', 'No live answer'), ('s02', 'Stopped at gatekeeper'), ('s03', 'Hung up in the opener'), ('s04', 'Refused right after the opener'),
          ('s05', 'Heard the pitch, disengaged'), ('s06', 'Real conversation'), ('s07', 'Objection, not overcome'), ('s08', 'Objection overcome, no ask'),
          ('s09', 'Meeting asked, declined'), ('s10', 'Meeting agreed'), ('s11', 'Date and time set'), ('s12', 'Invite confirmed')]
# From the daily "CAS Results" email (Barb Peterson, week of Nov 2-6, 2026). Two blocks: "Quantum" matches Patrick's seat
# (124 transfers in October = Patrick's 124 ConnectAndSell conversations) and "Coastal" matches the Mackenzie seat (450 vs 449).
DIAL = {'Patrick': {'Oct': dict(dials=7135, transfers=124, convs=92, meetings=9, assigned=84.0, on_dialer=37.58),
                    'Nov 2-6': dict(dials=3420, transfers=44, convs=32, meetings=3, assigned=20.0, on_dialer=16.01)},
        'Mackenzie': {'Oct': dict(dials=18247, transfers=450, convs=285, meetings=4, assigned=84.0, on_dialer=81.91),
                      'Nov 2-6': dict(dials=4835, transfers=106, convs=72, meetings=1, assigned=20.0, on_dialer=20.05)}}


def svg_grouped(rows, series, width=980, label_w=250, row_h=30):
    """rows: [(label, [v1, v2...])] values are percentages; series: [(name, color)]."""
    h = len(rows) * ((row_h - 6) * len(series) + 10) + 34
    mx = max((v for _, vs in rows for v in vs), default=1) or 1
    bw = width - label_w - 70
    o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="Where calls end, by rep" style="display:block">' % (width, h)]
    x = label_w
    for i, (nm, col) in enumerate(series):
        o.append('<rect x="%d" y="4" width="12" height="12" rx="3" fill="%s"/><text x="%d" y="14" font-size="12.5" fill="var(--mute)">%s</text>' % (x + i * 170, col, x + i * 170 + 18, e(nm)))
    y = 30
    for label, vs in rows:
        o.append('<text x="%d" y="%d" text-anchor="end" font-size="13" fill="var(--ink)">%s</text>' % (label_w - 12, y + row_h * len(series) / 2 - 4, e(label)))
        for j, v in enumerate(vs):
            w = max(2, bw * v / mx)
            o.append('<rect x="%d" y="%d" width="%.1f" height="%d" rx="4" fill="%s"/><text x="%.1f" y="%d" font-size="12" font-weight="600" fill="var(--ink)">%.1f%%</text>' % (
                label_w, y + j * (row_h - 6), w, row_h - 10, series[j][1], label_w + w + 8, y + j * (row_h - 6) + row_h - 18, v))
        y += (row_h - 6) * len(series) + 10
    o.append('</svg>')
    return ''.join(o).replace('height="%d"' % h, 'height="%d"' % y, 1) if False else ''.join(o)


def svg_funnel(steps, width=980):
    """steps: [(label, n)] -> funnel with step-to-step conversion. Narrow widths use left-aligned bars."""
    if width < 700:
        top = steps[0][1] or 1; bh, gap = 38, 8; h = len(steps) * (bh + gap) + 4; x0 = 128; maxw = width - x0 - 118
        cols = ['#0b7a6c', '#2a8f7f', '#4aa393', '#c28b2c', '#b26a00', '#b3352b']
        o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="Funnel" style="display:block">' % (width, h)]
        for i, (lab, n) in enumerate(steps):
            w = max(46, maxw * (n / top) ** 0.5) if n else 46; y = 2 + i * (bh + gap)
            o.append('<text x="%d" y="%d" text-anchor="end" font-size="13" fill="var(--ink)">%s</text>' % (x0 - 10, y + 24, e(lab)))
            o.append('<rect x="%d" y="%d" width="%.1f" height="%d" rx="7" fill="%s"/><text x="%.1f" y="%d" text-anchor="middle" font-size="14" font-weight="700" fill="#fff">%s</text>' % (x0, y, w, bh, cols[i % len(cols)], x0 + w / 2, y + 24, format(n, ',')))
            if i:
                prev = steps[i - 1][1]; pcn = 100 * n / prev if prev else 0
                r = ('1 in %d (%.1f%%)' % (round(prev / n), pcn)) if n and prev / n >= 2 else ('%.0f%% continue' % pcn)
                o.append('<text x="%.1f" y="%d" font-size="12.5" font-weight="600" fill="var(--mute)">%s</text>' % (x0 + w + 8, y + 24, r))
        o.append('</svg>'); return ''.join(o)
    top = steps[0][1] or 1; bh, gap = 46, 10; h = len(steps) * (bh + gap) + 6; cx = width / 2 - 20; maxw = width - 520
    cols = ['#0b7a6c', '#2a8f7f', '#4aa393', '#c28b2c', '#b26a00', '#b3352b', '#7a2a2a']
    o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="Funnel" style="display:block">' % (width, h)]
    for i, (lab, n) in enumerate(steps):
        w = max(34, maxw * (n / top) ** 0.5) if n else 34   # square-root scale so small steps stay visible
        y = 3 + i * (bh + gap)
        o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" rx="8" fill="%s"/>' % (cx - w / 2, y, w, bh, cols[i % len(cols)]))
        o.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="16" font-weight="700" fill="#fff">%s</text>' % (cx, y + 29, format(n, ',')))
        o.append('<text x="%.1f" y="%d" text-anchor="end" font-size="13.5" fill="var(--ink)">%s</text>' % (cx - maxw / 2 - 14, y + 28, e(lab)))
        if i:
            prev = steps[i - 1][1]; pcn = 100 * n / prev if prev else 0
            r = ('1 in %d (%.1f%%)' % (round(prev / n), pcn)) if n and prev / n >= 2 else ('%.0f%% continue' % pcn)
            o.append('<text x="%.1f" y="%d" font-size="13.5" font-weight="600" fill="var(--mute)">%s</text>' % (cx + maxw / 2 + 16, y + 28, r))
    o.append('</svg>')
    return ''.join(o)


def svg_cols(pairs, color='var(--accent)', width=520, height=190, ylab=''):
    n = len(pairs); mx = max((v for _, v in pairs), default=1) or 1; bw = (width - 40) / max(n, 1)
    o = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" style="display:block">' % (width, height)]
    for i, (lab, v) in enumerate(pairs):
        hgt = (height - 56) * v / mx; x = 30 + i * bw
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="4" fill="%s"/>' % (x + 6, height - 30 - hgt, bw - 12, hgt, color))
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="12" font-weight="600" fill="var(--ink)">%s</text>' % (x + bw / 2, height - 34 - hgt, v))
        o.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="11.5" fill="var(--mute)">%s</text>' % (x + bw / 2, height - 10, e(lab)))
    o.append('</svg>')
    return ''.join(o)



CSS = """:root{--bg:#f4f3ee;--panel:#fffefb;--ink:#1a2320;--mute:#5f6b66;--line:#dcdad0;--line2:#ebe9e0;--accent:#0b7a6c;--warn:#b26a00;--bad:#b3352b;--c3:#3f5fa8;--good:#1c7c4a;--shadow:0 1px 2px rgba(20,30,25,.06),0 6px 18px rgba(20,30,25,.05)}
@media (prefers-color-scheme:dark){:root{--bg:#0e1412;--panel:#151d1a;--ink:#e7eeea;--mute:#98a8a0;--line:#29342f;--line2:#202a26;--accent:#3fc7b0;--warn:#e8a541;--bad:#ff8f84;--c3:#8fa9e8;--good:#63d596;--shadow:none}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Avenir Next","Segoe UI",system-ui,-apple-system,sans-serif}
.top{background:linear-gradient(120deg,#0d2a25,#123b34 60%,#0b2a3a);color:#eaf5f1;padding:34px 24px 30px}.in{max-width:1100px;margin:0 auto}
.top h1{margin:0 0 8px;font-size:clamp(26px,4vw,38px);letter-spacing:-.02em;line-height:1.12}.top p{margin:0;max-width:78ch;color:#b9d3cb}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:22px}.kpi{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:26px;letter-spacing:-.02em;font-variant-numeric:tabular-nums;color:#fff}.kpi span{font-size:12.5px;color:#a9c8be}
main{max-width:1100px;margin:0 auto;padding:24px 20px 80px}section{margin-bottom:38px}h2{font-size:22px;margin:0 0 6px;letter-spacing:-.01em}h3{margin:0 0 8px;font-size:15px}
.lede{color:var(--mute);margin:0 0 14px;max-width:80ch}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow);min-width:0}.card+.card{margin-top:14px}
.two{align-items:start;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.br{display:grid;grid-template-columns:minmax(110px,200px) minmax(60px,1fr) 100px;gap:10px;align-items:center;margin:5px 0;font-size:13px}.tr{background:var(--line2);border-radius:4px;height:14px;display:block}.fl{display:block;height:14px;border-radius:4px}.nm{text-align:right;color:var(--mute);white-space:nowrap}
table.sc td.c{text-align:center;vertical-align:middle}table.sc td{vertical-align:top}table{border-collapse:collapse;width:100%;font-size:13.5px;display:block;overflow-x:auto;max-width:100%}.card{overflow-x:auto}th{text-align:left;color:var(--mute);font-weight:600;padding:5px 10px 5px 0}td{padding:6px 10px 6px 0;border-top:1px solid var(--line2)}td.n{font-variant-numeric:tabular-nums}td.n i{color:var(--mute);font-style:normal;font-size:12px}
.big{font-size:30px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}.good{color:var(--good)}.bad{color:var(--bad)}.warn{color:var(--warn)}
blockquote{margin:8px 0;padding:8px 12px;border-left:3px solid var(--accent);background:var(--line2);border-radius:0 8px 8px 0;font-size:13.5px}blockquote small{display:block;color:var(--mute);margin-top:2px}
.fix{counter-reset:f;list-style:none;padding:0;margin:0}.fix li{counter-increment:f;padding:12px 14px 12px 48px;position:relative;background:var(--panel);border:1px solid var(--line);border-radius:12px;margin-bottom:10px}
.fix li:before{content:counter(f);position:absolute;left:14px;top:12px;width:24px;height:24px;border-radius:99px;background:var(--accent);color:#fff;text-align:center;font-weight:700;font-size:13px;line-height:24px}
.note{color:var(--mute);font-size:12.5px;margin-top:8px}"""


def audit_matrix(C, per):
    ok = lambda s_, c_: '<span style="display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:700;color:#fff;background:%s">%s</span>' % (c_, s_)
    P_, N_, F_, U_ = ok('Pass', 'var(--good)'), ok('Neutral', 'var(--warn)'), ok('Fail', 'var(--bad)'), ok('Not measured', 'var(--mute)')
    dv = lambda a, b: a / b if b else None
    def band(v, pass_if, neutral_if):
        return U_ if v is None else P_ if pass_if(v) else N_ if neutral_if(v) else F_
    rows = [('Conversion rate', 'Meetings per conversation', 'Over 5%', '3% to 5%', 'Under 3%', lambda a: dv(a['meetings'], a['convs']), lambda v: '%.1f%%' % (100 * v), lambda v: v > .05, lambda v: v >= .03),
            ('D2C: dials per conversation', 'Dials it takes to get one real conversation', '1 to 10', '11 to 20', 'Over 20', lambda a: dv(a['dials'], a['convs']), lambda v: '%.0f' % v, lambda v: v <= 10, lambda v: v <= 20),
            ('D2M: dials per meeting', 'Dials it takes to book one meeting', 'Under 400', '400 to 700', 'Over 700', lambda a: dv(a['dials'], a['meetings']), lambda v: format(round(v), ','), lambda v: v < 400, lambda v: v <= 700),
            ('Quick hang-up', 'Share of conversations logged this way', 'Under 10%', '', 'Over 10%', lambda a: dv(a['qh'], a['transfers']), lambda v: '%.0f%%' % (100 * v), lambda v: v <= .10, lambda v: False),
            ('No pitch', 'Share of conversations logged this way', 'Under 10%', '', 'Over 10%', lambda a: dv(a['nop'], a['transfers']), lambda v: '%.0f%%' % (100 * v), lambda v: v <= .10, lambda v: False),
            ('Do Not Call', 'Share of conversations', 'Under 5%', '', 'Over 5%', lambda a: dv(a['dnc'], a['transfers']), lambda v: '%.1f%%' % (100 * v), lambda v: v <= .05, lambda v: False),
            ('Disqualified', 'Share of conversations', 'Under 5%', '', 'Over 5%', lambda a: dv(a['dq'], a['transfers']), lambda v: '%.1f%%' % (100 * v), lambda v: v <= .05, lambda v: False)]
    hrs_ = {}
    if per:
        for seat, key in (('Kenzie Braun seat', 'Mackenzie'), ('Patrick Dodge', 'Patrick')):
            d_ = DIAL[key][per]; hrs_[seat] = dict(mph=d_['meetings'] / d_['on_dialer'], wrap=None)
    rows.append(('Meetings per hour', 'Meetings per hour on the dialer', 'Over 0.41', '0.25 to 0.40', 'Under 0.25', lambda a: None, None, None, None))
    out = []
    for lab, sub, p_, n_, f_, fn, fmt, pf, nf in rows:
        cells = []
        for seat in ('Kenzie Braun seat', 'Patrick Dodge'):
            if lab == 'Meetings per hour':
                v = hrs_.get(seat, {}).get('mph')
                cells.append('<td class="n">%s %s</td>' % ('%.2f' % v if v is not None else '-', band(v, lambda x: x > .41, lambda x: x >= .25) if v is not None else U_))
            else:
                v = fn(C['audit'][seat]); cells.append('<td class="n">%s %s</td>' % (fmt(v) if v is not None else '-', band(v, pf, nf)))
        out.append('<tr><td><b>%s</b><br><span class="note">%s</span></td><td class="note">%s</td><td class="note">%s</td><td class="note">%s</td>%s</tr>' % (e(lab), e(sub), p_, n_ or '-', f_, ''.join(cells)))
    out.append('<tr><td><b>Meeting show rate</b><br><span class="note">Held meetings out of booked</span></td><td class="note">65%% or more</td><td class="note">50%% to 59%%</td><td class="note">Under 50%%</td><td class="n" colspan="2">%s (needs the Zoom check, planned for later)</td></tr>' % U_)
    return ('<section id="matrix"><h2>SBAAS audit matrix</h2><p class="lede">The Sales Blitz standards from the playbook, scored for each caller. Dials, conversations and meetings come from the ConnectAndSell log for this period; the dialing-hours row is shown only for months where the daily report covers the whole period.</p>'
            '<div class="card"><table class="sc"><tr><th>Measure</th><th>Pass</th><th>Neutral</th><th>Fail</th><th>Mackenzie seat</th><th>Patrick</th></tr>%s</table>'
            '<p class="note">A "conversation" here is every logged outcome except Quick Hang-up, Blocked by Gatekeeper and Voicemail Pick-up, which reproduces the daily report\'s count for October (285 and 92). The playbook lists D2M as "&gt; 400 Pass"; the intent is clearly "under 400". Show rate and wrap time are not computed from this data.</p></div></section>' % ''.join(out))


def page(M, since, C, until=None, HC=None):
    K, Pt, T = M['Kenzie Braun'], M['Patrick Dodge'], M['total']
    KS, PS = 'Mackenzie seat', 'Patrick Dodge'
    today = datetime.date.today().strftime('%b %-d, %Y')
    d0 = datetime.date.fromisoformat(since).strftime('%b %-d')
    s = ('since ' + d0) if not until else 'between %s and %s' % (d0, datetime.date.fromisoformat(until).strftime('%b %-d'))
    cs = C['seat']; ks, kp = cs.get('Kenzie Braun seat', (0, 0)), cs.get('Patrick Dodge', (0, 0))
    if since <= '2026-10-01' and (not until or until >= '2026-10-31'): per, PLAB = 'Oct', 'October'
    elif '2026-11-01' <= since <= '2026-11-02' and (not until or until >= '2026-11-06'): per, PLAB = 'Nov 2-6', 'the week of Nov 2-6'
    else: per, PLAB = None, ''
    has_h = per is not None
    DP, DM = (DIAL['Patrick'][per], DIAL['Mackenzie'][per]) if per else ({}, {})
    hrs = lambda d_: '%.0f of %.0f hours' % (d_['on_dialer'], d_['assigned'])
    pct_ = lambda a_, b_: round(100 * a_ / b_, 1) if b_ else 0.0
    mph = lambda d_: d_['meetings'] / d_['on_dialer']
    kask, kpitch = K['funnel'][4][1], K['funnel'][3][1]
    L = M['listen']; lk = lambda ids: ' '.join('<a href="https://app.hubspot.com/contacts/20682069/record/0-48/%s" target="_blank" rel="noopener">%s</a>' % (i, i) for i in ids) or 'none in this window'
    h = []
    # ---------------- top band
    h.append('<div class="top"><div class="in"><h1>Why we are not booking more meetings</h1><p>Every ConnectAndSell conversation %s, plus an AI read of the %d that have a full transcript. Two callers work our lists: the Mackenzie seat (an outsourced calling team) and Patrick. This page shows where each one loses the call. Updated %s.</p>' % (s, T['n'], today))
    h.append('<div class="kpis"><div class="kpi"><b>%d</b><span>conversations logged by ConnectAndSell %s</span></div><div class="kpi"><b>%d</b><span>meetings scheduled (%.1f%% of conversations)</span></div>'
             '<div class="kpi"><b>%d of %d</b><span>Mackenzie seat: meetings per conversation (%.1f%%)</span></div><div class="kpi"><b>%d of %d</b><span>Patrick: meetings per conversation (%.1f%%)</span></div>'
             '<div class="kpi"><b>%d of %d</b><span>booked meetings with the invite confirmed</span></div></div></div></div><main>' % (
                 C['n'], s, C['meet'], pct_(C['meet'], C['n']), ks[1], ks[0], pct_(ks[1], ks[0]), kp[1], kp[0], pct_(kp[1], kp[0]), T['confirmed'], T['booked']))
    mper = per if ((per == 'Oct' and until and until <= '2026-10-31') or per == 'Nov 2-6') else None
    h.append(audit_matrix(C, mper))
    # ---------------- how to read
    h.append('<section id="read"><h2>How to read these numbers</h2><div class="card"><table class="sc"><tr><th>Term</th><th>What it means here</th></tr>'
             '<tr><td><b>Dial</b></td><td>One outbound call attempt.</td></tr>'
             '<tr><td><b>Transfer</b></td><td>A live answer the dialer hands to a rep. This is the dialer team\'s daily count.</td></tr>'
             '<tr><td><b>Conversation (dialer report)</b></td><td>A transfer where a real exchange happened, not a hang-up or gatekeeper.</td></tr>'
             '<tr><td><b>Conversation (ConnectAndSell log)</b></td><td>Every call logged against a seat with an outcome. For Patrick this is the same number as his transfers. For the Mackenzie seat it is the same as the other block\'s transfers (about 450 in October).</td></tr>'
             '<tr><td><b>Mackenzie seat</b></td><td>The outsourced calling team. Callers on it introduce themselves with different first names, which is why they differ from call to call. In the daily report it is the block for the other account.</td></tr>'
             '<tr><td><b>Patrick</b></td><td>Quantum\'s own seat, the "Quantum" block in the daily report.</td></tr></table>'
             '<p class="note">The match is on counts: Patrick has 124 conversations in October and the report shows 124 transfers; the Mackenzie seat has 449 and the report shows 450, with 4 meetings each way.</p></div></section>')
    # ---------------- where calls get lost
    fp = [('Dials', DP['dials']), ('Transfers', DP['transfers']), ('Real conversations', DP['convs']), ('Meetings set', DP['meetings'])] if has_h else []
    fm = [('Dials', DM['dials']), ('Transfers', DM['transfers']), ('Real conversations', DM['convs']), ('Meetings set', DM['meetings'])] if has_h else []
    series = [('Mackenzie seat', 'var(--warn)'), ('Patrick Dodge', 'var(--accent)')]
    rows_ = [(lab, [M['stage']['Kenzie Braun seat'][i], M['stage']['Patrick Dodge'][i]]) for i, (_, lab) in enumerate(STAGES)]
    h.append('<section id="lost"><h2>Where calls get lost</h2><p class="lede">The same journey for each caller, from the first dial to the meeting.</p>')
    if has_h:
        h.append('<div class="card"><h3>1. From dial to meeting, @@P@@ (daily dialer report)</h3><div class="two"><div><h3 style="color:var(--warn)">Mackenzie seat</h3>%s<p class="note">1 transfer per %d dials. %.1f%% of conversations became a meeting. %s</p></div>'
                 '<div><h3 style="color:var(--accent)">Patrick</h3>%s<p class="note">1 transfer per %d dials. %.1f%% of conversations became a meeting. %s</p></div></div></div>' % (
                     svg_funnel(fm, 520), round(DM['dials'] / DM['transfers']), pct_(DM['meetings'], DM['convs']), 'Dialed ' + hrs(DM) + '.',
                     svg_funnel(fp, 520), round(DP['dials'] / DP['transfers']), pct_(DP['meetings'], DP['convs']), 'Dialed ' + hrs(DP) + '.'))
    h.append('<div class="card" style="margin-top:14px"><h3>%s. Where each call ends (AI-scored stage reached, %d transcribed calls)</h3>%s<p class="note">Each bar is the share of that caller\'s calls that ended at that stage. The Mackenzie seat piles up at the opener; Patrick\'s calls reach "meeting asked" far more often.</p></div>'
             '<div class="card" style="margin-top:14px"><h3>%s. How far calls get once a person is on the line (all %d transcribed calls)</h3>%s<p class="note">Bar widths use a square-root scale so small late steps stay visible. The numbers and "1 in N" ratios are exact.</p></div></section>' % (
                 '2' if has_h else '1', T['n'], svg_grouped(rows_, series), '3' if has_h else '2', T['n'], svg_funnel(M['allfunnel'])))
    # ---------------- two levers
    if has_h:
        half = DM['convs'] * (DP['meetings'] / DP['convs']) / 2; l1 = half - DM['meetings']
        l2 = (DP['assigned'] - DP['on_dialer']) * mph(DP)
        h.append('<section id="levers"><h2>The two biggest levers</h2><p class="lede">Neither needs a new list or a new tool.</p><div class="two">'
                 '<div class="card"><h3>1. Mackenzie seat: convert the conversations it already has</h3><div class="big warn">+%.0f meetings</div><p>It used %s in @@P@@ and had %d conversations, but booked %d (%.1f%%), or %.2f per dialing hour. If it reached just half of Patrick\'s rate (%.1f%%), the same period would have had about %.0f more meetings.</p></div>'
                 '<div class="card"><h3>2. Patrick: use the dialing hours we are assigned</h3><div class="big warn">+%.0f meetings</div><p>He used %s in @@P@@ (%.0f%%) and booked %d, or %.2f per dialing hour. The other %.0f assigned hours at the same rate is about %.0f meetings.</p></div></div>'
                 '<p class="note">Patrick\'s rate is not a guarantee for the other seat: his conversations include people we already know. Treat the first number as a target to test, not a forecast.</p></section>' % (
                     l1, hrs(DM), DM['convs'], DM['meetings'], pct_(DM['meetings'], DM['convs']), mph(DM), pct_(DP['meetings'], DP['convs']) / 2, l1,
                     l2, hrs(DP), pct_(DP['on_dialer'], DP['assigned']), DP['meetings'], mph(DP), DP['assigned'] - DP['on_dialer'], l2))
    # ---------------- short version
    items = []
    if has_h:
        items.append('<li><b>The Mackenzie seat uses its hours and wastes the conversations.</b> %.0f%% of its assigned time was dialed in @@P@@, and %.1f%% of its conversations became meetings (%.2f per hour; the playbook passes at 0.41).</li>' % (pct_(DM['on_dialer'], DM['assigned']), pct_(DM['meetings'], DM['convs']), mph(DM)))
        items.append('<li><b>Patrick converts, but uses only %.0f%% of his assigned hours.</b> That is %.2f meetings per dialing hour in @@P@@.</li>' % (pct_(DP['on_dialer'], DP['assigned']), mph(DP)))
    longc, longm = C['talk'].get('Over 90 seconds', (0, 0)); sh = sum(C['talk'][k][0] for k in C['talk_order'][:2])
    items.append('<li><b>Half of all conversations are over in 20 seconds.</b> %d of %d lasted 20 seconds or less and none booked. Conversations past 90 seconds booked %d of %d.</li>' % (sh, C['n'], longm, longc))
    items.append('<li><b>The ask is missing on the Mackenzie seat.</b> %d asks across %d calls (%.0f%%); %d reached the pitch and only %d of them included an ask.</li>' % (K['asks'], K['n'], pct_(K['asks'], K['n']), kpitch, kask))
    items.append('<li><b>Closing language is what books.</b> Patrick\'s plain asks: %d, booked %d. Asks with an alternative or assumptive close: %d, booked %d.</li>' % (Pt['asks_plain'], Pt['booked_plain'], Pt['asks_close'], Pt['booked_close']))
    items.append('<li><b>The opener and the objections.</b> %.0f%% of live conversations on the Mackenzie seat end in the opener, and %.0f%% of its objections get no real response.</li>' % (pct_(K['hung'], K['live']), pct_(K['ob_not'], K['ob'])))
    if C.get('people'):
        items.append('<li><b>The same people keep picking up.</b> %d conversations came from %d different people; the typical person had already been called about %d times.</li>' % (C['n'], C['people'], C['prior_med']['Kenzie Braun seat']))
    h.append('<section><h2>The short version</h2><div class="card"><ol class="fix" style="margin:0">%s</ol></div></section>' % ''.join(items))
    # ---------------- dialing hours
    if has_h:
        h.append('<section><h2>Dialing hours</h2><p class="lede">Each caller is assigned 20 hours a week. The daily report shows how much of that is actually spent on the dialer (%s).</p><div class="two">'
                 '<div class="card"><h3>Mackenzie seat</h3><div class="big good">%s</div><p>%.0f%% of assigned time. It produced %d meetings, %.2f per dialing hour.</p></div>'
                 '<div class="card"><h3>Patrick</h3><div class="big warn">%s</div><p>%.0f%% of assigned time. It produced %d meetings, %.2f per dialing hour.%s</p></div></div>'
                 '<p class="note">Source: the daily "CAS Results" emails from Barb Peterson, copied from the two blocks of that report.</p></section>' % (
                     PLAB, hrs(DM), pct_(DM['on_dialer'], DM['assigned']), DM['meetings'], mph(DM), hrs(DP), pct_(DP['on_dialer'], DP['assigned']), DP['meetings'], mph(DP),
                     ' Barb noted the week was about 4 hours short.' if per == 'Nov 2-6' else ''))
    if HC: h.append(hubspot_calls_html(HC))
    # ---------------- what ConnectAndSell shows
    tk, to = C['talk'], C['talk_order']
    h.append('<section><h2>What ConnectAndSell itself shows</h2><p class="lede">ConnectAndSell logged <b>%d conversations</b> %s and <b>%d "Meeting scheduled"</b> (%.1f%%).</p>'
             '<div class="two"><div class="card"><h3>Most conversations are over in seconds</h3><table><tr><th>Talk time</th><th>Conversations</th><th>Meetings</th></tr>%s</table>'
             '<p class="note">%d of %d (%.0f%%) lasted 20 seconds or less and none booked. Past 90 seconds, %d of %d booked. Part of that is simply that booking takes time, so read it as "short calls never get a chance".</p></div>'
             '<div class="card"><h3>How the conversations ended</h3>%s</div></div>'
             '<div class="card" style="margin-top:14px"><h3>People we know book far better than people who only picked up once</h3><table><tr><th>List type</th><th>Conversations</th><th>Meetings</th><th>Rate</th></tr>%s</table>'
             '<p class="note">"Relationship" lists: Deal Follow-Up, All Time Meetings, Hot List, No-Shows, Hubspot Follow Up. "Picked up before" lists, like "Callable - Best Bets", are built from people who answered a call once. Most relationship-list calls are Patrick\'s, so this is also partly a caller effect.</p></div>'
             '<div class="card" style="margin-top:14px"><h3>Biggest lists</h3><table><tr><th>List</th><th>Conversations</th><th>Meetings</th><th>Rate</th></tr>%s</table></div></section>' % (
                 C['n'], s, C['meet'], pct_(C['meet'], C['n']), ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>' % (k, tk[k][0], tk[k][1]) for k in to),
                 sh, C['n'], pct_(sh, C['n']), longm, longc, bars([(k, v) for k, v in C['disp'].most_common(10)], C['n'], 'var(--c3)'),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%.1f%%</td></tr>' % ('Relationship lists' if n == 'warm' else 'Picked-up-before lists', C['temp'][n][0], C['temp'][n][1], pct_(C['temp'][n][1], C['temp'][n][0])) for n in ('warm', 'cold')),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%.1f%%</td></tr>' % (e(k), n_, m_, pct_(m_, n_)) for k, n_, m_ in C['lists'])))
    # ---------------- repeat
    if C.get('people'):
        ag, fs = C['again'], C['first']
        h.append('<section><h2>The same people keep picking up</h2><p class="lede">%d conversations came from only <b>%d different people</b>; %d people connected more than once.</p><div class="two">'
                 '<div class="card"><div class="big warn">%d</div><p>was the typical number of earlier calls already logged to each person we connected with (Mackenzie seat %d, Patrick %d). %.0f%% of conversations were with someone called 25 or more times before. That counts every dial.</p></div>'
                 '<div class="card"><h3>First connect vs connecting again</h3><table><tr><th></th><th>First time</th><th>Again</th></tr><tr><td>Conversations</td><td class="n">%d</td><td class="n">%d</td></tr><tr><td>Quick hang-up</td><td class="n">%.0f%%</td><td class="n">%.0f%%</td></tr><tr><td>No pitch given</td><td class="n">%.0f%%</td><td class="n">%.0f%%</td></tr><tr><td>Median talk time</td><td class="n">%ds</td><td class="n">%ds</td></tr><tr><td>Meetings</td><td class="n">%d (%.1f%%)</td><td class="n">%d (%.1f%%)</td></tr></table></div></div>'
                 '<p class="note">Of the %d "Do Not Call" outcomes, %d had any call logged to that person afterwards.</p></section>' % (
                     C['n'], C['people'], C['multi'], C['prior_med']['Kenzie Braun seat'], C['prior_med']['Kenzie Braun seat'], C['prior_med']['Patrick Dodge'], C['prior25'],
                     fs['n'], ag['n'], fs['hang'], ag['hang'], fs['nop'], ag['nop'], fs['talk'], ag['talk'], fs['meet'], fs['rate'], ag['meet'], ag['rate'], C['dnc'][0], C['dnc'][1]))
    # ---------------- what we learn on the calls
    oc = M['objcount']; ko, po = oc['Kenzie Braun'], oc['Patrick Dodge']; kn, pn = sum(ko.values()), sum(po.values()); sg = M['sig']
    UNK = {'not asked / unclear', 'not_discussed', 'not discussed', 'unclear', 'not_mentioned', 'not mentioned', 'unknown'}
    def top(c, n=6):
        kn_ = {k: v for k, v in c.items() if k not in UNK}; tot = sum(kn_.values()) or 1
        return bars([(k.replace('_', ' ').title(), v) for k, v in sorted(kn_.items(), key=lambda kv: -kv[1])[:n]], tot, 'var(--c3)') + '<p class="note">%d of %d calls had an answer; the rest did not come up.</p>' % (sum(kn_.values()), sum(c.values()))
    ob5 = lambda o_, n_, col: bars([('%s objection%s' % ('3+' if k == 3 else k, '' if k == 1 else 's'), o_.get(k, 0)) for k in (0, 1, 2, 3)], max(n_, 1), col)
    h.append('<section><h2>What we learn on the calls</h2><p class="lede">What the AI pulled out of the %d transcripts.</p>'
             '<div class="two"><div class="card"><h3>Objections per call</h3>%s<p class="note">Mackenzie seat (%d calls), %.2f per call.</p>%s<p class="note">Patrick (%d calls), %.2f per call.</p></div><div class="card"><h3>Prospect interest by the end of the call</h3>%s</div></div>'
             '<div class="two" style="margin-top:14px"><div class="card"><h3>Do they use HubSpot?</h3>%s</div><div class="card"><h3>Budget</h3>%s</div></div>'
             '<div class="two" style="margin-top:14px"><div class="card"><h3>CRM they named</h3>%s</div><div class="card"><h3>Already outsourcing?</h3><p class="note">Appointment setting</p>%s<p class="note" style="margin-top:10px">Marketing</p>%s</div></div></section>' % (
                 T['n'], ob5(ko, kn, 'var(--warn)'), kn, sum(k * v for k, v in ko.items()) / max(kn, 1), ob5(po, pn, 'var(--accent)'), pn, sum(k * v for k, v in po.items()) / max(pn, 1),
                 top(M['interest']), top(sg['hubspot_status']), top(sg['budget_status']), top(sg['crm_name'], 7), top(sg['outsources_appt_setting'], 4), top(sg['outsources_marketing'], 4)))
    wk_ = C['weeks']
    h.append('<section><h2>Week by week</h2><div class="two"><div class="card"><h3>Conversations logged per week</h3>%s</div><div class="card"><h3>Meetings scheduled per week</h3>%s</div></div><p class="note">ConnectAndSell conversation log. The last week may be partial.</p></section>' % (
        svg_cols([(k, v[0]) for k, v in wk_]), svg_cols([(k, v[1]) for k, v in wk_], 'var(--good)')))
    # ---------------- playbook scorecard
    ok = lambda s_, c_: '<span style="display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:700;color:#fff;background:%s">%s</span>' % (c_, s_)
    G_, A_, R_ = ok('Meets', 'var(--good)'), ok('Watch', 'var(--warn)'), ok('Below', 'var(--bad)')
    tot = sum(v[0] for v in C['temp'].values()); warmn = C['temp'].get('warm', (0, 0))[0]
    sc = []
    if has_h:
        sc += [('Dial hours used', '80% or more of the dedicated time', 'Mackenzie seat %.0f%%, Patrick %.0f%% (@@P@@).' % (pct_(DM['on_dialer'], DM['assigned']), pct_(DP['on_dialer'], DP['assigned'])), R_ if DP['on_dialer'] / DP['assigned'] < .8 else G_),
               ('Live conversations per rep-hour', '8 to 12 on a blitz hour', 'About %.1f conversations per dialing hour for the Mackenzie seat and %.1f for Patrick (dialer report counts, @@P@@).' % (DM['convs'] / DM['on_dialer'], DP['convs'] / DP['on_dialer']), R_),
               ('Meetings per hour', 'Pass over 0.41, neutral 0.25 to 0.40, fail under 0.25', 'Mackenzie seat %.2f, Patrick %.2f (@@P@@).' % (mph(DM), mph(DP)), R_)]
    sc += [('No pitch / quick hang-up', 'A "no pitch" is ours to fix: fix the greeting, measure pitch rate', '%.0f%% of conversations ended "No Pitch - Quick Hang Up" (Mackenzie seat %.0f%%, Patrick %.0f%%). The pitch was heard on %.0f%% of Mackenzie-seat calls and %.0f%% of Patrick\'s.' % (C['nopitch_all'], C['nopitch']['Kenzie Braun seat'], C['nopitch']['Patrick Dodge'], M['pitch']['Kenzie Braun'], M['pitch']['Patrick Dodge']), R_)]
    if C.get('people'):
        sc.append(('Cap the attempts, rest and recycle', 'Agree a maximum, space the attempts, move exhausted contacts to email or LinkedIn', 'Typical person connected with had about %d earlier calls; %.0f%% of conversations were with someone called 25+ times; %d of %d people connected more than once.' % (C['prior_med']['Kenzie Braun seat'], C['prior25'], C['multi'], C['people']), R_))
    sc += [('Start with the warmest lists (Revenue Efficiency Model)', 'Keep, Grow, Multiply, Convert, then Expand', 'Only %.0f%% of conversations came from relationship lists, and just %d of the Mackenzie seat\'s %d. They book at 7.9%% against 1.2%% on the rest.' % (pct_(warmn, tot), C['seat_temp'].get(('Kenzie Braun seat', 'warm'), (0, 0))[0], ks[0]), R_),
           ('Ask, and leave with a dated next step', 'Never end a call without a dated next step', 'A meeting or callback was set on %.0f%% of Mackenzie-seat calls and %.0f%% of Patrick\'s.' % (M['next']['Kenzie Braun'], M['next']['Patrick Dodge']), R_),
           ('Ask earlier (test it)', 'Track the second the ask happens and test earlier', 'When the Mackenzie seat asks, it is about %d%% of the way through the call; Patrick asks at about %d%%.' % (M['askpos']['Kenzie Braun'], M['askpos']['Patrick Dodge']), A_),
           ('Aim at the decision maker', 'Define target titles; use gatekeepers as a route to one', 'A decision maker was confirmed on %d of %d calls; "not the decision maker" came up on %d.' % (M['dm_yes'], T['n'], M['notdm']), R_),
           ('Validate the list', 'Check employment before a blitz; log invalid contacts separately', '%d conversations (%.0f%%) were retired or no longer at the company.' % (C['retired'], pct_(C['retired'], C['n'])), A_),
           ('Follow-up queue used', 'Check how many live connects go to follow-up', '%.0f%% of conversations were logged Follow-Up.' % C['followup'], G_)]
    if len(C['slot']) >= 3:
        sc.append(('Direct and mobile numbers', 'Prefer them and test call windows', 'Calls that connected on a primary number ended "No Pitch" %.0f%%; secondary %.0f%%; tertiary %.0f%%.' % tuple(x[2] for x in C['slot'][:3]), A_))
    tr = ''.join('<tr><td><b>%s</b><br><span class="note">%s</span></td><td>%s</td><td class="c">%s</td></tr>' % (e(a_), e(b_), e(c_), v) for a_, b_, c_, v in sc)
    h.append('<section id="playbook"><h2>Checked against the Sales Blitz Playbook</h2><p class="lede">The playbook on thequantumleap.business sets the standards we sell. Here is how our own seats measure against each.</p><div class="card"><table class="sc"><tr><th>Standard</th><th>Our numbers</th><th>Status</th></tr>%s</table></div>'
             '<div class="card" style="margin-top:14px"><h3>Fields the playbook says to capture</h3><div class="two"><div><b class="good">Already captured on every call</b><p class="note">True outcome (stage reached), decision maker, opener quality, pitch made, objections and how they were handled, ask and confirmation, second of the ask, interest, next step.</p></div><div><b class="warn">Not yet captured</b><p class="note">Quick hang-up reason, attempt count and last attempt date, rest-until date, employment verified on, target title tier, no-show recovery attempts.</p></div></div></div></section>' % tr)
    h.append('<section><h2>Calls worth listening to</h2><p class="lede">The playbook says to review recordings before acting on a quick-hang-up number. These are HubSpot call records; open one to hear the recording.</p><div class="two"><div class="card"><h3>Hung up in the opener (Mackenzie seat)</h3><p class="note">Listen to the first ten seconds.</p><p>%s</p></div><div class="card"><h3>Pitch heard, no ask (Mackenzie seat)</h3><p class="note">Where could the ask have gone in?</p><p>%s</p></div></div><div class="card" style="margin-top:14px"><h3>Calls that booked a meeting</h3><p>%s</p></div></section>' % (lk(L['hang']), lk(L['missed']), lk(L['booked'])))
    # ---------------- findings
    h.append('<section><h2>The funnel, side by side</h2><p class="lede">Percentages are of all transcribed calls for that caller (the AI read). Its booking counts can differ slightly from ConnectAndSell\'s.</p><div class="card">%s</div></section>' % funnel_table(M))
    h.append('<section><h2>Finding 1: the meeting is rarely asked for on the Mackenzie seat</h2><div class="two"><div class="card"><h3>Mackenzie seat</h3>%s</div><div class="card"><h3>Patrick</h3>%s</div></div></section>' % (
        bars([('Never asked', K['never']), ('Asked (any point)', K['asks'])], max(K['n'], 1), 'var(--bad)'), bars([('Never asked', Pt['never']), ('Asked (any point)', Pt['asks'])], max(Pt['n'], 1), 'var(--c3)')))
    h.append('<section><h2>Finding 2: only closing language books meetings</h2><p class="lede">Same caller, same kind of calls: what he says at the ask decides the result.</p><div class="two"><div class="card"><div class="big bad">%d of %d</div><p>plain asks booked (for example "would you be open to a call?"), both callers combined.</p></div><div class="card"><div class="big good">%d of %d</div><p>asks with an alternative or assumptive close booked.</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>What the booking calls sound like (Patrick)</h3>'
             '<blockquote>"Would it make sense to just put a placeholder on the calendar in mid-November and then I could just follow up the week before and confirm the time?"<small>Assumptive close on a "not now" answer</small></blockquote>'
             '<blockquote>"Are mornings or afternoons typically better for you? ... You are central time, right? How about 10:00?"<small>Alternative close, then a specific time</small></blockquote>'
             '<blockquote>"What if I sent you an invite to connect for like 15 minutes and we could kind of talk through it then? Would that work?"<small>Small ask, then "how is 1:00 for you?"</small></blockquote>'
             '<p class="note">Patrick uses a close on %d of his %d asks (%.0f%%). The Mackenzie seat used one on %d of %d calls. Quotes are lightly cleaned from the transcripts.</p></div></section>' % (
                 Pt['asks_plain'] + K['asks_plain'], Pt['booked_plain'] + K['booked_plain'], Pt['asks_close'] + K['asks_close'], Pt['booked_close'] + K['booked_close'], Pt['asks_close'], Pt['asks'], pct_(Pt['asks_close'], Pt['asks']), K['asks_close'], K['n']))
    ob = lambda R: bars([(OBJ.get(k, k), v) for k, v in R['objs'].most_common(7)], sum(R['objs'].values()) or 1, 'var(--warn)')
    h.append('<section><h2>Finding 3: the opener and the objections</h2><div class="two"><div class="card"><h3>Where live conversations end (Mackenzie seat)</h3>%s<p class="note">Of %d people reached.</p></div><div class="card"><h3>Opener quality (AI-scored)</h3>%s</div></div>'
             '<div class="card" style="margin-top:14px"><h3>What the opener sounds like</h3><blockquote>"I\'m calling with Quantum Business Solutions ... I know I\'m an interruption here, but mind if I grab half a minute to let you know why I called?" ... "we help companies improve their sales process through CRM solutions and lead generation."<small>Typical Mackenzie-seat opener: polite, but generic.</small></blockquote>'
             '<p>Openers that acknowledge the interruption are associated with fewer immediate hang-ups (%.0f%% vs %.0f%%), but calls that end early never get to say the line, so it is a hint to test, not proof.</p></div>'
             '<div class="two" style="margin-top:14px"><div class="card"><h3>Objections raised (Mackenzie seat)</h3>%s<p class="note">%d objections: %d not handled (%.0f%%), %d handled well.</p></div><div class="card"><h3>Objections raised (Patrick)</h3>%s<p class="note">%d objections: %d not handled (%.0f%%), %d handled well.</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>Typical missed recoveries</h3><blockquote>Prospect: "I am on a call right now, try me again next week." Rep: "Sure. Let me send you some information via email."<small>A call-back request turned into an email, with no time locked in.</small></blockquote><blockquote>Prospect: "All right, I appreciate the call but no need for your services." Rep: "Not interested? Okay, then."<small>Ends the call at the first no.</small></blockquote></div></section>' % (
                 bars([('Hung up in the opener', K['hung']), ('Refused right after', K['refused']), ('Stayed past the opener', max(K['live'] - K['hung'] - K['refused'], 0))], max(K['live'], 1), 'var(--bad)'), K['live'],
                 bars([(k.replace('_', ' ').title(), v) for k, v in K['opener'].most_common()], max(K['n'], 1), 'var(--c3)'), M['interrupt']['a_hang'], M['interrupt']['b_hang'],
                 ob(K), K['ob'], K['ob_not'], pct_(K['ob_not'], K['ob']), K['ob_good'], ob(Pt), Pt['ob'], Pt['ob_not'], pct_(Pt['ob_not'], Pt['ob']), Pt['ob_good']))
    h.append('<section><h2>Who we reach, and what happens after a booking</h2><div class="two"><div class="card"><h3>Decision maker identified</h3><table><tr><th></th><th>Mackenzie seat</th><th>Patrick</th></tr><tr><td>Yes</td><td class="n">%d</td><td class="n">%d</td></tr><tr><td>No</td><td class="n">%d</td><td class="n">%d</td></tr><tr><td>Never established</td><td class="n">%d</td><td class="n">%d</td></tr></table></div>'
             '<div class="card"><h3>Bookings that stick</h3><div class="big warn">%d of %d</div><p>booked meetings have a confirmed invite. The rest rely on a prospect remembering a verbal agreement.</p></div></div></section>' % (
                 K['dm']['yes'], Pt['dm']['yes'], K['dm']['no'], Pt['dm']['no'], K['dm']['unclear'], Pt['dm']['unclear'], T['confirmed'], T['booked']))
    h.append('<section><h2>What to try, built from the calls that worked</h2><p class="lede">Drafts to test, not scripts to read word for word. Change one thing at a time and watch the numbers on this page.</p><div class="two">'
             '<div class="card"><h3>The ask (every conversation past the opener)</h3><blockquote>"The reason I am calling is to set up 15 minutes to talk through your sales and marketing priorities. Are mornings or afternoons usually better for you?"</blockquote><blockquote>"I will send a quick invite. Does Tuesday at 10 or Thursday at 2 work better?"</blockquote></div>'
             '<div class="card"><h3>When they say "no time" or "call me back"</h3><blockquote>"Totally understand. That is exactly why I am asking for 15 minutes next week. Would Tuesday or Thursday be better?"</blockquote></div>'
             '<div class="card"><h3>When they say "not interested"</h3><blockquote>"Fair enough. Can I ask what you are using today for your CRM? I will not take more than a minute."</blockquote></div>'
             '<div class="card"><h3>The opener</h3><p>Lead with something specific to them (their CRM, a recent change, a prior conversation) in the first sentence, then the permission line. Test two or three versions against the share that hang up in the opener (now %.0f%% on the Mackenzie seat).</p></div></div></section>' % pct_(K['hung'], K['live']))
    fix = []
    if has_h:
        fix += ['<li><b>Coach the Mackenzie seat on the ask and the close.</b> It already dials its hours; the gap is converting the conversations. Use the closing lines above on every conversation that gets past the opener.</li>',
                '<li><b>Get Patrick\'s dialing hours up to the assigned 20 a week.</b> At the current rate that is the cheapest lever on the page.</li>']
    fix += ['<li><b>Spend dialing time on people we know first.</b> Relationship lists book at about 8%% of conversations against about 1%% on the picked-up-before lists.</li>',
            '<li><b>Rewrite and A/B test the opener</b> with a specific reason up front, and track the share that hang up in it.</li>',
            '<li><b>Give both callers a one-line recovery for each top objection.</b> "No time" and "call back later" should end with a time on the calendar, not an email.</li>',
            '<li><b>Confirm the invite on the call.</b> Only %d of %d bookings are confirmed.</li>' % (T['confirmed'], T['booked']),
            '<li><b>Rest the people who keep picking up.</b> Cap the attempts and move exhausted contacts to email or LinkedIn.</li>',
            '<li><b>Establish the decision maker early</b> and ask for a warm transfer or the right name when it is someone else.</li>']
    h.append('<section><h2>What to change, in order</h2><ol class="fix">%s</ol></section>' % ''.join(fix))
    h.append('<section><h2>How this was measured</h2><div class="card"><p>ConnectAndSell logs every conversation with an outcome, a talk time and the list it came from. For every call %s that has a transcript in HubSpot, an AI read the full transcript for the stage reached, the opener, whether and how a meeting was asked for, and the objections and how they were handled. "Booked" means the call reached a meeting agreed, a time set or an invite confirmed. Parts of many transcripts are masked for dual-consent reasons, so the prospect side is incomplete. Dial, transfer and hours figures come from the daily "CAS Results" emails. Percentages are shares of calls, not of people.</p></div></section></main>' % s)
    doc = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Why we are not booking more meetings</title><style>%s</style></head><body>%s</body></html>' % (CSS, ''.join(h))
    return doc.replace('@@P@@', PLAB)


def hubspot_calls(since, until=None):
    """Outbound calls placed from HubSpot itself (not ConnectAndSell): count, outcome, talk time, by owner."""
    own = {o['id']: (o.get('firstName', '') + ' ' + o.get('lastName', '')).strip() for o in hs('GET', '/crm/v3/owners?limit=500')['results']}
    disp = {d['id']: d['label'] for d in hs('GET', '/calling/v1/dispositions')}
    t0 = datetime.datetime.fromisoformat(since); t1 = (datetime.datetime.fromisoformat(until) + datetime.timedelta(days=1)) if until else datetime.datetime.utcnow() + datetime.timedelta(days=2)
    rows, w = [], t0
    while w < t1:
        w2, after = min(w + datetime.timedelta(days=14), t1), 0
        while True:
            r = hs('POST', '/crm/v3/objects/calls/search', {'filterGroups': [{'filters': [
                {'propertyName': 'hs_object_source_detail_1', 'operator': 'NEQ', 'value': 'ConnectAndSell'},
                {'propertyName': 'hs_call_direction', 'operator': 'EQ', 'value': 'OUTBOUND'},
                {'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': str(int(w.timestamp() * 1000))},
                {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': str(int(w2.timestamp() * 1000))}]}],
                'limit': 100, 'after': after, 'properties': ['hubspot_owner_id', 'hs_call_duration', 'hs_call_disposition', 'hs_timestamp', 'hs_call_source']})
            rows += r['results']; nx = (r.get('paging') or {}).get('next', {}).get('after')
            if not nx: break
            after = nx
        w = w2
    out = []
    for x in rows:
        p = x['properties']
        out.append(dict(owner=own.get(p.get('hubspot_owner_id'), 'Other'), dur=(int(p['hs_call_duration']) / 1000 if p.get('hs_call_duration') else 0), disp=disp.get(p.get('hs_call_disposition'), 'No outcome logged'), id=x['id']))
    return out


def hubspot_calls_html(H):
    if not H: return ''
    n = len(H); conn = [c for c in H if c['disp'] == 'Connected' or c['dur'] >= 30]; long_ = [c for c in H if c['dur'] >= 60]
    byo = collections.Counter(c['owner'] for c in H).most_common(4)
    dc = collections.Counter(c['disp'] for c in H)
    med = round(st.median([c['dur'] for c in H if c['dur']] or [0]))
    rows = ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td></tr>' % (e(o), k, sum(1 for c in H if c['owner'] == o and c['dur'] >= 60), sum(1 for c in H if c['owner'] == o and c['disp'] == 'Connected')) for o, k in byo)
    return ('<section id="hubspot-calls"><h2>Calls made from HubSpot (outside ConnectAndSell)</h2><p class="lede">Some calls are placed straight from HubSpot. They do not appear in the dialer report or the numbers above, so they are shown separately.</p>'
            '<div class="two"><div class="card"><div class="big">%d</div><p>outbound calls from HubSpot in this period. %d reached a person or ran 30 seconds or more, and %d lasted over a minute (%.0f%%). Median talk time %d seconds.</p><table><tr><th>Who</th><th>Calls</th><th>Over 1 min</th><th>Logged Connected</th></tr>%s</table></div>'
            '<div class="card"><h3>Outcome logged in HubSpot</h3>%s</div></div></section>' % (
                n, len(conn), len(long_), pc(len(long_), n), med, rows, bars([(k, v) for k, v in dc.most_common(8)], n, 'var(--c3)')))


# ---------------------------------------------------------------- tabbed report: windows + history
TAB_CSS = """.tabsbar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.tabsbar b{margin-right:6px;font-size:13px;color:var(--mute);text-transform:uppercase;letter-spacing:.08em}
.tabsbar label{padding:6px 14px;border:1px solid var(--line);border-radius:99px;cursor:pointer;font-size:13.5px;background:var(--panel);color:var(--mute)}
input.tab{position:absolute;opacity:0;pointer-events:none}.win{display:none}
%s"""


def history_data(since='2022-01-01'):
    own = {o['id']: (o.get('firstName', '') + ' ' + o.get('lastName', '')).strip() for o in hs('GET', '/crm/v3/owners?limit=500')['results']}
    props = ['hs_timestamp', 'hubspot_owner_id'] + [P + k for k in ('stage_reached', 'opener', 'asked_for_meeting', 'alternative_close', 'assumptive_close', 'objections', 'objection_handling', 'invite_confirmed')]
    rows, w, end = [], datetime.datetime.fromisoformat(since), datetime.datetime.utcnow() + datetime.timedelta(days=2)
    while w < end:
        w2, after = w + datetime.timedelta(days=14), 0
        while True:
            r = hs('POST', '/crm/v3/objects/calls/search', {'filterGroups': [{'filters': [
                {'propertyName': P + 'stage_reached', 'operator': 'HAS_PROPERTY'},
                {'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': str(int(w.timestamp() * 1000))},
                {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': str(int(w2.timestamp() * 1000))}]}], 'limit': 100, 'after': after, 'properties': props})
            rows += [dict(x['properties'], rep=own.get(x['properties'].get('hubspot_owner_id'), 'Other')) for x in r['results']]
            nx = (r.get('paging') or {}).get('next', {}).get('after')
            if not nx: break
            after = nx
        w = w2
    return rows


def history_html(H):
    n = len(H); asked = sum(g(p, 'asked_for_meeting') == 'yes' for p in H); bk = sum(booked(p) for p in H)
    first = min(p['hs_timestamp'][:7] for p in H); inv = sum(g(p, 'invite_confirmed') == 'yes' for p in H if booked(p))
    mo = collections.defaultdict(list)
    for p in H: mo[p['hs_timestamp'][:7]].append(p)
    months = sorted(mo)[-24:]
    rate = lambda f: [(datetime.datetime.strptime(m, '%Y-%m').strftime("%b '%y"), round(100 * sum(map(f, mo[m])) / len(mo[m]), 1)) for m in months if len(mo[m]) >= 20]
    reps = collections.Counter(p['rep'] for p in H); top4 = [r for r, c in reps.most_common(4) if c >= 100]
    cols = ['var(--accent)', 'var(--warn)', 'var(--c3)', '#8a5aa8']
    series = [(r, cols[i]) for i, r in enumerate(top4)]
    rows_ = [(lab, [pc(sum(stg(p) == k for p in H if p['rep'] == r), sum(1 for p in H if p['rep'] == r)) for r in top4]) for k, lab in STAGES]
    ob = collections.Counter(o for p in H for o in (g(p, 'objections') or '').split(';') if o and o != 'none')
    hd = collections.Counter(g(p, 'objection_handling') for p in H if g(p, 'objection_handling') in ('not_handled', 'partial', 'handled_well'))
    rep_rows = ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%.1f%%</td><td class="n">%.1f%%</td><td class="n">%.1f%%</td></tr>' % (
        e(r), sum(1 for p in H if p['rep'] == r), pc(sum(g(p, 'asked_for_meeting') == 'yes' for p in H if p['rep'] == r), sum(1 for p in H if p['rep'] == r)),
        pc(sum(close(p) for p in H if p['rep'] == r), sum(1 for p in H if p['rep'] == r)), pc(sum(booked(p) for p in H if p['rep'] == r), sum(1 for p in H if p['rep'] == r))) for r in top4)
    o = ['<div class="top"><div class="in"><h1>History: every scored call</h1><p>%s conversations read end to end since %s. This is the baseline for any new client: run it on their old calls first, then watch the weekly and monthly tabs move against it.</p>' % (format(n, ','), first)]
    o.append('<div class="kpis"><div class="kpi"><b>%s</b><span>calls scored</span></div><div class="kpi"><b>%.1f%%</b><span>asked for a meeting</span></div><div class="kpi"><b>%.1f%%</b><span>reached a booked meeting</span></div><div class="kpi"><b>%d of %d</b><span>booked meetings with the invite confirmed</span></div></div></div></div><main>' % (format(n, ','), pc(asked, n), pc(bk, n), inv, bk))
    o.append('<section><h2>Trend by month</h2><p class="lede">Months with at least 20 scored calls.</p><div class="two"><div class="card"><h3>Meeting asked for (%% of calls)</h3>%s</div><div class="card"><h3>Reached a booked meeting (%% of calls)</h3>%s</div></div></section>' % (
        svg_cols(rate(lambda p: g(p, 'asked_for_meeting') == 'yes'), 'var(--c3)', 980, 200), svg_cols(rate(booked), 'var(--good)', 980, 200)))
    o.append('<section><h2>Where calls ended, by rep (all time)</h2><div class="card">%s</div><div class="card" style="margin-top:14px"><table><tr><th>Rep</th><th>Calls scored</th><th>Asked</th><th>Closing language used</th><th>Booked</th></tr>%s</table></div></section>' % (svg_grouped(rows_, series), rep_rows))
    o.append('<section><h2>Objections, all time</h2><div class="two"><div class="card"><h3>What they say</h3>%s</div><div class="card"><h3>How they were handled</h3>%s</div></div></section></main>' % (
        bars([(OBJ.get(k, k), v) for k, v in ob.most_common(9)], sum(ob.values()) or 1, 'var(--warn)'), bars([(k.replace('_', ' ').title(), v) for k, v in hd.most_common()], sum(hd.values()) or 1, 'var(--accent)')))
    return ''.join(o)


def window_body(since, until, label):
    D = load(since, until); M = metrics(D); C = cas_metrics(since, until); doc = page(M, since, C, until, hubspot_calls(since, until))
    body = doc[doc.index('<div class="top">'):doc.index('</main>') + 7]
    return body, D, M


def report(windows=None):
    today = datetime.date.today()
    windows = windows or [('Last 7 days', str(today - datetime.timedelta(days=7)), None), ('Last 30 days', str(today - datetime.timedelta(days=30)), None),
                          ('October', '2026-10-01', '2026-10-31'), ('November so far', '2026-11-02', None),
                          ('Since Sep 28 (baseline)', '2026-09-28', None), ('History', None, None)]
    bodies = []
    for label, since, until in windows:
        if since is None:
            bodies.append((label, history_html(history_data())))
        else:
            b, D, M = window_body(since, until, label); bodies.append((label, b)); print(label, 'calls', len(D), 'booked', M['total']['booked'])
    n = len(bodies); css = ''.join('#t%d:checked ~ #w%d{display:block}#t%d:checked ~ .tabsbar label[for=t%d]{background:var(--accent);color:#fff;border-color:var(--accent)}' % (i, i, i, i) for i in range(n))
    d = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Call Analysis: where we lose meetings</title><style>%s%s</style></head><body>' % (CSS, TAB_CSS % css)]
    d += ['<input class="tab" type="radio" name="tab" id="t%d"%s>' % (i, ' checked' if i == 0 else '') for i in range(n)]
    d.append('<div class="tabsbar"><b>View</b>%s</div>' % ''.join('<label for="t%d">%s</label>' % (i, e(l)) for i, (l, _) in enumerate(bodies)))
    d += ['<div class="win" id="w%d">%s</div>' % (i, b) for i, (_, b) in enumerate(bodies)]
    d.append('</body></html>')
    return ''.join(d)



AUDIT_PROPOSAL_ID = os.environ.get('CI_AUDIT_PROPOSAL_ID', 'ce0087c8-a1fc-4e50-abd2-e9ab9dbfa71b')


def publish_report(proposal_id=None):
    """Rebuild every tab and write it to the ClientCommand audit page."""
    import ssl, urllib.request
    doc = report()
    ctx = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt')
    req = urllib.request.Request(os.environ['CLIENTCOMMAND_URL'], json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'set_web_proposal_custom_html',
        'arguments': {'proposal_id': proposal_id or AUDIT_PROPOSAL_ID, 'html': doc}}}).encode(), {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, method='POST')
    raw = urllib.request.urlopen(req, context=ctx, timeout=180).read().decode()
    return {'published': 'custom' in raw, 'chars': len(doc)}


if __name__ == '__main__':
    since = sys.argv[sys.argv.index('--since') + 1] if '--since' in sys.argv else '2026-09-28'
    if '--publish' in sys.argv:
        print(publish_report()); sys.exit(0)
    if '--report' in sys.argv:
        doc = report()
    else:
        D = load(since); M = metrics(D); C = cas_metrics(since); doc = page(M, since, C, None, hubspot_calls(since))
    open('/tmp/meetings_page.html', 'w').write(doc)
    print('html', len(doc), '-> /tmp/meetings_page.html')
