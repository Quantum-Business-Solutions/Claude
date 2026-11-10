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


def load(since):
    own = {o['id']: (o.get('firstName', '') + ' ' + o.get('lastName', '')).strip() for o in hs('GET', '/crm/v3/owners?limit=500')['results']}
    rows, w = [], datetime.datetime.fromisoformat(since)
    end = datetime.datetime.utcnow() + datetime.timedelta(days=2)
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
                      dur=round(st.median(dur)) if dur else 0, talk=round(st.median([float(g(p, 'rep_talk_pct')) for p in R if g(p, 'rep_talk_pct')])),
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
    M['listen'] = dict(hang=[p['id'] for p in rs.sample([p for p in D if p['rep'] == 'Kenzie Braun' and stg(p) == 's03'], 8)],
                       missed=[p['id'] for p in rs.sample([p for p in D if p['rep'] == 'Kenzie Braun' and g(p, 'got_to_pitch') == 'yes' and g(p, 'asked_for_meeting') != 'yes' and g(p, 'prospect_interest') in ('neutral', 'warm')], 8)],
                       booked=[p['id'] for p in D if booked(p)][:8])
    sg = lambda k: collections.Counter((p.get('ai__signal_' + k) or 'not asked / unclear').lower() for p in D)
    M['sig'] = {k: sg(k) for k in ('hubspot_status', 'crm_name', 'budget_status', 'outsources_appt_setting', 'outsources_marketing')}
    M['interest'] = collections.Counter(g(p, 'prospect_interest') for p in D)
    M['interrupt'] = dict(a=len(inter), a_hang=pc(sum(stg(p) == 's03' for p in inter), len(inter)), b=len(rest), b_hang=pc(sum(stg(p) == 's03' for p in rest), len(rest)))
    M['total'] = dict(n=len(D), booked=sum(booked(p) for p in D), confirmed=sum(g(p, 'invite_confirmed') == 'yes' for p in D if booked(p)))
    return M


WARM = re.compile(r'follow[- ]?up|all time meetings|hot list|no-shows|meetings|client', re.I)


def cas_metrics(since):
    from cas_sync import conversations
    cv = conversations(since, datetime.date.today().isoformat())
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
    C['talk_order'] = order
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
    C['prior_med'] = {s_: round(st.median([p_ for p_, x in zip(pr_, cv) if (x['UserName'].startswith('Patrick')) == (s_ == 'Patrick Dodge')])) for s_ in ('Patrick Dodge', 'Kenzie Braun seat')}
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
# From the daily "CAS Results" email (Barb Peterson, week of Nov 2-6, 2026): Quantum block, October and November month-to-date
DIAL = {'Oct': dict(dials=7135, transfers=124, convs=92, meetings=9, assigned=84.0, on_dialer=37.58),
        'Nov 2-6': dict(dials=3420, transfers=44, convs=32, meetings=3, assigned=20.0, on_dialer=16.01)}


def svg_grouped(rows, series, width=980, label_w=250, row_h=30):
    """rows: [(label, [v1, v2...])] values are percentages; series: [(name, color)]."""
    h = len(rows) * (row_h * len(series) // 1 + 8) + 34
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
    """steps: [(label, n)] -> centred funnel with step-to-step conversion."""
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


def matrix(C):
    rows = []
    for seat in ('Kenzie Braun seat', 'Patrick Dodge'):
        cells = []
        for tmp in ('warm', 'cold'):
            n, m = C['seat_temp'].get((seat, tmp), (0, 0)); cells.append('<td class="n">%d of %d <i>%.1f%%</i></td>' % (m, n, pc(m, n)))
        rows.append('<tr><td>%s</td>%s</tr>' % (seat, ''.join(cells)))
    return '<table><tr><th>Meetings per conversation</th><th>Relationship lists</th><th>Picked-up-before lists</th></tr>%s</table>' % ''.join(rows)


def page(M, since, C):
    K, Pt, T = M['Kenzie Braun'], M['Patrick Dodge'], M['total']
    kb, pb = K['funnel'][5][1], Pt['funnel'][5][1]
    today = datetime.date.today().strftime('%b %-d, %Y'); s = datetime.date.fromisoformat(since).strftime('%b %-d')
    wk = ''.join('<tr><td>Week of %s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td></tr>' % (
        k, K_[0], K_[1], K_[2], P_[0], P_[1], P_[2]) for (k, K_), (_, P_) in zip(
            K['weeks'], Pt['weeks'] + [('', [0, 0, 0])] * (len(K['weeks']) - len(Pt['weeks']))))
    kask = K['funnel'][4][1]; kpitch = K['funnel'][3][1]
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Why we are not booking more meetings</title><style>%s</style></head><body>' % CSS]
    h.append('<div class="top"><div class="in"><h1>Why we are not booking more meetings</h1><p>Every ConnectAndSell conversation since %s, plus an AI read of the %d that have a full transcript: what Kenzie Braun\'s seat and Patrick Dodge say, where conversations end, and what is different about the ones that booked. Updated %s.</p>' % (s, T['n'], today))
    cs, ct = C['seat'], C['temp']
    ks, kp = cs.get('Kenzie Braun seat', (0, 0)), cs.get('Patrick Dodge', (0, 0))
    h.append('<div class="kpis"><div class="kpi"><b>%d</b><span>conversations logged by ConnectAndSell since %s</span></div><div class="kpi"><b>%d</b><span>meetings scheduled (%.1f%%)</span></div><div class="kpi"><b>%.1f%%</b><span>Patrick: %d of %d conversations</span></div><div class="kpi"><b>%.1f%%</b><span>Kenzie seat: %d of %d conversations</span></div><div class="kpi"><b>%d of %d</b><span>booked meetings with the invite confirmed</span></div></div></div></div><main>' % (
        C['n'], s, C['meet'], pc(C['meet'], C['n']), pc(kp[1], kp[0]), kp[1], kp[0], pc(ks[1], ks[0]), ks[1], ks[0], T['confirmed'], T['booked']))
    pr = lambda a, b: pc(a, b)
    tk = C['talk']; to = C['talk_order']
    short = sum(tk[k][0] for k in to[:2]); longc, longm = tk['Over 90 seconds']
    h.append('<section><h2>What ConnectAndSell itself shows</h2><p class="lede">Before the AI read of the calls: ConnectAndSell logged <b>%d conversations</b> since %s and <b>%d "Meeting scheduled"</b> (%.1f%%). Two things stand out, and neither is about the script.</p>'
             '<div class="two"><div class="card"><h3>Conversations get nowhere because most are over in seconds</h3><table><tr><th>Talk time</th><th>Conversations</th><th>Meetings</th></tr>%s</table>'
             '<p class="note">%d of %d conversations (%.0f%%) lasted 20 seconds or less, and none of them booked. Conversations past 90 seconds booked %d of %d (%.0f%%): a 1-in-5 rate once someone actually stays on. (Part of that is simply that booking takes time, so read it as "short calls never get a chance", not "long calls cause meetings".)</p></div>'
             '<div class="card"><h3>People we know book far better than people who only picked up once</h3><table><tr><th>List type</th><th>Conversations</th><th>Meetings</th><th>Rate</th></tr>%s</table>'
             '<p class="note">"Relationship" = lists of people we already know: Deal Follow-Up, All Time Meetings, Hot List, No-Shows, Hubspot Follow Up. "Picked up before" = lists built from people who have answered a call, like "Callable - Best Bets". The Kenzie seat spent %d of %d conversations there.</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>Is it the lists or the rep? Both.</h3>%s<p class="note">Same list type, different rep: on picked-up-before lists Patrick books about 3 times as often as the Kenzie seat. Same rep, different list: Patrick books about 3 times as often on relationship lists as on picked-up-before ones. The Kenzie seat had too few relationship-list conversations to compare.</p></div><div class="card" style="margin-top:14px"><h3>How the conversations ended (ConnectAndSell disposition)</h3>%s</div>'
             '<div class="card" style="margin-top:14px"><h3>Biggest lists</h3><table><tr><th>List</th><th>Conversations</th><th>Meetings</th><th>Rate</th></tr>%s</table></div></section>' % (
                 C['n'], s, C['meet'], pr(C['meet'], C['n']),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>' % (k, tk[k][0], tk[k][1]) for k in to),
                 short, C['n'], pr(short, C['n']), longm, longc, pr(longm, longc),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%.1f%%</td></tr>' % ('Relationship lists' if n == 'warm' else 'Picked-up-before lists', C['temp'][n][0], C['temp'][n][1], pr(C['temp'][n][1], C['temp'][n][0])) for n in ('warm', 'cold') if n in C['temp']),
                 C['k_cold'][0], C['k_cold'][1], matrix(C),
                 bars([(k, v) for k, v in C['disp'].most_common(10)], C['n'], 'var(--c3)'),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%.1f%%</td></tr>' % (e(k), n, m, pr(m, n)) for k, n, m in C['lists'])))
    ag, fs = C['again'], C['first']
    h.append('<section><h2>The same people keep picking up</h2><p class="lede">The "connections" are not new people. %d conversations came from only <b>%d different people</b>, and %d people connected more than once.</p>'
             '<div class="two"><div class="card"><div class="big warn">%d</div><p>was the typical number of earlier calls already logged to each person we connected with (Kenzie seat %d, Patrick %d). %.0f%% of conversations were with someone who had been called 25 or more times before. That counts every dial, including voicemails and no-answers.</p></div>'
             '<div class="card"><h3>First connect vs coming back to the same person</h3><table><tr><th></th><th>First time in this window</th><th>Connected again</th></tr><tr><td>Conversations</td><td class="n">%d</td><td class="n">%d</td></tr><tr><td>Quick hang-up</td><td class="n">%.0f%%</td><td class="n">%.0f%%</td></tr><tr><td>No pitch given</td><td class="n">%.0f%%</td><td class="n">%.0f%%</td></tr><tr><td>Median talk time</td><td class="n">%ds</td><td class="n">%ds</td></tr><tr><td>Meetings</td><td class="n">%d (%.1f%%)</td><td class="n">%d (%.1f%%)</td></tr></table></div></div>'
             '<div class="card" style="margin-top:14px"><p>What this means: the pool of people who pick up is small and we are calling it over and over. Second and third connects with the same person are shorter and end without a pitch more often (%.0f%% vs %.0f%%). A bigger or fresher pool, with a rest period for people we have already connected with, is likely to help as much as any script change.</p><p class="note">Good news on compliance: of the %d "Do Not Call" outcomes, %d had any call logged to that person afterwards.</p></div></section>' % (
                 C['n'], C['people'], C['multi'], C['prior_med']['Kenzie Braun seat'], C['prior_med']['Kenzie Braun seat'], C['prior_med']['Patrick Dodge'], C['prior25'],
                 fs['n'], ag['n'], fs['hang'], ag['hang'], fs['nop'], ag['nop'], fs['talk'], ag['talk'], fs['meet'], fs['rate'], ag['meet'], ag['rate'],
                 ag['nop'], fs['nop'], C['dnc'][0], C['dnc'][1]))
    # ---- charts: where calls get lost ----
    O, N_ = DIAL['Oct'], DIAL['Nov 2-6']
    pct_ = lambda a, b: round(100 * a / b, 1) if b else 0
    fun_d = [('Dials', O['dials']), ('Transfers to a rep', O['transfers']), ('Real conversations', O['convs']), ('Meetings set', O['meetings'])]
    fun_c = [(l, n) for l, n in M['allfunnel']]
    series = [('Kenzie Braun seat', 'var(--warn)'), ('Patrick Dodge', 'var(--accent)')]
    rows_ = [(lab, [M['stage']['Kenzie Braun seat'][i], M['stage']['Patrick Dodge'][i]]) for i, (_, lab) in enumerate(STAGES)]
    hrs = lambda d_: '%.0f of %.0f hours' % (d_['on_dialer'], d_['assigned'])
    h.append('<section id="lost"><h2>Where calls get lost</h2><p class="lede">Three views of the same problem, from the first dial to the booked meeting.</p>'
             '<div class="card"><h3>1. From dial to meeting (October, from the daily CAS results report)</h3>%s'
             '<p class="note">%s dials produced %d transfers (1 per %d dials), %d real conversations and %d meetings set: about 1 meeting per %d dials and %.1f%% of conversations. Week of Nov 2-6: %s dials, %d transfers, %d conversations, %d meetings. "Transfer" and "conversation" are the dialer team\'s own counts, so they are smaller than the ConnectAndSell conversation log used elsewhere on this page.</p></div>'
             '<div class="card" style="margin-top:14px"><h3>2. Where each call ends, by rep (AI-scored stage reached, %d calls)</h3>%s<p class="note">Each bar is the share of that rep\'s calls that ended at that stage. The Kenzie seat piles up at "Hung up in the opener" and "Objection, not overcome"; Patrick\'s calls reach "Meeting asked" far more often.</p></div>'
             '<div class="card" style="margin-top:14px"><h3>3. How far calls get once a person is on the line (all %d transcribed calls)</h3>%s<p class="note">Bar widths use a square-root scale so the small late steps stay visible; the numbers and the "1 in N" ratios are exact.</p></div></section>' % (
                 svg_funnel(fun_d), format(O['dials'], ','), O['transfers'], round(O['dials'] / O['transfers']), O['convs'], O['meetings'], round(O['dials'] / max(O['meetings'], 1)), pct_(O['meetings'], O['convs']),
                 format(N_['dials'], ','), N_['transfers'], N_['convs'], N_['meetings'], T['n'], svg_grouped(rows_, series), T['n'], svg_funnel(fun_c)))
    h.append('<section><h2>Dialing hours: we are not using the time we have</h2><p class="lede">Each week the dialer team is assigned 20 hours for Quantum. The daily results report shows how much of that is actually spent on the dialer.</p>'
             '<div class="two"><div class="card"><h3>October</h3><div class="big warn">%s</div><p>spent on the dialer. That is %.0f%% of the assigned time, and it produced %d meetings, or %.2f per dialing hour.</p></div>'
             '<div class="card"><h3>Week of Nov 2-6</h3><div class="big warn">%s</div><p>%.0f%% of assigned time. Barb noted the week was about 4 hours short of the scheduled dialing for Quantum, while the other account on the same report got its full 20 hours.</p></div></div>'
             '<div class="card" style="margin-top:14px"><p>At October\'s rate of %.2f meetings per dialing hour, the full 84 assigned hours would have produced about %.0f meetings instead of %d. Dialing hours are the cheapest lever on this page: no script change, no new list.</p><p class="note">Source: the daily "CAS Results" emails from Barb Peterson. Numbers are copied from the Quantum block of that report.</p></div></section>' % (
                 hrs(O), pct_(O['on_dialer'], O['assigned']), O['meetings'], O['meetings'] / O['on_dialer'], hrs(N_), pct_(N_['on_dialer'], N_['assigned']),
                 O['meetings'] / O['on_dialer'], O['meetings'] / O['on_dialer'] * O['assigned'], O['meetings']))
    oc = M['objcount']; ko, po = oc['Kenzie Braun'], oc['Patrick Dodge']
    kn, pn = sum(ko.values()), sum(po.values())
    sg = M['sig']
    UNK = {'not asked / unclear', 'not_discussed', 'not discussed', 'unclear', 'not_mentioned', 'not mentioned', 'unknown'}
    def top(c, n=6):
        kn_ = {k: v for k, v in c.items() if k not in UNK}; tot = sum(kn_.values()) or 1
        return bars([(k.replace('_', ' ').title(), v) for k, v in sorted(kn_.items(), key=lambda kv: -kv[1])[:n]], tot, 'var(--c3)') + '<p class="note">%d of %d calls had an answer; the rest did not come up.</p>' % (sum(kn_.values()), sum(c.values()))
    h.append('<section><h2>What we learn on the calls</h2><p class="lede">Everything the AI pulled out of the %d transcripts: objections, interest, and what prospects told us about their tools and budget.</p>'
             '<div class="two"><div class="card"><h3>How many objections a call faces</h3>%s<p class="note">Kenzie seat (%d calls). Average %.2f objections per call.</p>%s<p class="note">Patrick (%d calls). Average %.2f per call.</p></div>'
             '<div class="card"><h3>Prospect interest by the end of the call</h3>%s</div></div>'
             '<div class="two" style="margin-top:14px"><div class="card"><h3>Do they use HubSpot?</h3>%s</div><div class="card"><h3>Budget</h3>%s</div></div>'
             '<div class="two" style="margin-top:14px"><div class="card"><h3>CRM they named</h3>%s</div><div class="card"><h3>Already outsourcing?</h3><p class="note">Appointment setting</p>%s<p class="note" style="margin-top:10px">Marketing</p>%s</div></div></section>' % (
                 len(D_) if False else T['n'],
                 bars([('%s objection%s' % ('3+' if k == 3 else k, '' if k == 1 else 's'), ko.get(k, 0)) for k in (0, 1, 2, 3)], max(kn, 1), 'var(--warn)'), kn, sum(k * v for k, v in ko.items()) / max(kn, 1),
                 bars([('%s objection%s' % ('3+' if k == 3 else k, '' if k == 1 else 's'), po.get(k, 0)) for k in (0, 1, 2, 3)], max(pn, 1), 'var(--accent)'), pn, sum(k * v for k, v in po.items()) / max(pn, 1),
                 top(M['interest']), top(sg['hubspot_status']), top(sg['budget_status']), top(sg['crm_name'], 7), top(sg['outsources_appt_setting'], 4), top(sg['outsources_marketing'], 4)))
    wk_ = C['weeks']
    h.append('<section><h2>Week by week</h2><div class="two"><div class="card"><h3>Conversations logged per week</h3>%s</div><div class="card"><h3>Meetings scheduled per week</h3>%s</div></div><p class="note">ConnectAndSell conversation log. The last week is partial.</p></section>' % (
        svg_cols([(k, v[0]) for k, v in wk_]), svg_cols([(k, v[1]) for k, v in wk_], 'var(--good)')))
    # ---- scorecard against the Sales Blitz Playbook ----
    ok = lambda s_, c_: '<span style="display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:700;color:#fff;background:%s">%s</span>' % (c_, s_)
    G, A, R = ok('Meets', 'var(--good)'), ok('Watch', 'var(--warn)'), ok('Below', 'var(--bad)')
    O_, N2 = DIAL['Oct'], DIAL['Nov 2-6']
    mph, mph2 = O_['meetings'] / O_['on_dialer'], N2['meetings'] / N2['on_dialer']
    tot = sum(v[0] for v in C['temp'].values()); warmn = C['temp'].get('warm', (0, 0))[0]
    kseat_warm = C['seat_temp'].get(('Kenzie Braun seat', 'warm'), (0, 0))[0]
    rows_sc = [
        ('Dial hours used', '80% or more of the dedicated blitz time', 'October %.0f%% (%s). Week of Nov 2-6: %.0f%%.' % (pc(O_['on_dialer'], O_['assigned']), hrs(O_), pc(N2['on_dialer'], N2['assigned'])), R if O_['on_dialer'] / O_['assigned'] < .8 else G),
        ('Live conversations per rep-hour', '8 to 12 on a blitz hour', 'About %.1f transfers and %.1f conversations per dialing hour in October (dialer team counts).' % (O_['transfers'] / O_['on_dialer'], O_['convs'] / O_['on_dialer']), R),
        ('Meetings per hour', 'Pass over 0.41, neutral 0.25 to 0.40, fail under 0.25', 'October %.2f, week of Nov 2-6 %.2f.' % (mph, mph2), R),
        ('No pitch / quick hang-up', 'A "no pitch" is ours to fix: fix the greeting, measure pitch rate', '%.0f%% of conversations ended "No Pitch - Quick Hang Up" (Kenzie seat %.0f%%, Patrick %.0f%%). The pitch was heard on %.0f%% of Kenzie-seat transcribed calls and %.0f%% of Patrick\'s.' % (C['nopitch_all'], C['nopitch']['Kenzie Braun seat'], C['nopitch']['Patrick Dodge'], M['pitch']['Kenzie Braun'], M['pitch']['Patrick Dodge']), R),
        ('Cap the attempts, rest and recycle', 'Agree a maximum, space the attempts, move exhausted contacts to email or LinkedIn', 'Typical person connected with had about %d earlier calls logged; %.0f%% of conversations were with someone called 25 or more times; %d of %d people connected more than once.' % (C['prior_med']['Kenzie Braun seat'], C['prior25'], C['multi'], C['people']), R),
        ('Start with the warmest lists (Revenue Efficiency Model)', 'Keep, Grow, Multiply, Convert, then Expand', 'Only %.0f%% of conversations came from relationship lists (Convert tier), and just %d of the Kenzie seat\'s %d. They book at 7.9%% against 1.2%% on the rest.' % (pc(warmn, tot), kseat_warm, C['seat'].get('Kenzie Braun seat', (0, 0))[0]), R),
        ('Ask, and leave with a dated next step', 'Never end a call without a dated next step', 'A meeting or callback was set on %.0f%% of Kenzie-seat calls and %.0f%% of Patrick\'s.' % (M['next']['Kenzie Braun'], M['next']['Patrick Dodge']), R),
        ('Ask earlier (test it)', 'Track the second the ask happens and test earlier', 'When the Kenzie seat asks, it is about %d%% of the way through the call; Patrick asks at about %d%%.' % (M['askpos']['Kenzie Braun'], M['askpos']['Patrick Dodge']), A),
        ('Aim at the decision maker', 'Define target titles; use gatekeepers as a route to one', 'A decision maker was confirmed on %d of %d calls; "not the decision maker" came up on %d.' % (M['dm_yes'], T['n'], M['notdm']), R),
        ('Validate the list', 'Check employment before a blitz; log invalid contacts separately', '%d conversations (%.0f%%) were retired or no longer at the company. The list-verification process can catch these before dialing.' % (C['retired'], pc(C['retired'], C['n'])), A),
        ('Follow-up queue used', 'Check how many live connects go to follow-up', '%.0f%% of conversations were logged Follow-Up.' % C['followup'], G),
        ('Peers on the same platform', 'When results drop, compare other teams on the same setup', 'The other account on the daily report booked 4 meetings from 285 conversations in October (1.4%%); ours booked %d from %d (%.1f%%). Both are low per dialing hour, so platform-wide causes (caller ID, carrier screening, the server migration) are worth ruling out.' % (O_['meetings'], O_['convs'], pc(O_['meetings'], O_['convs'])), A),
        ('Direct and mobile numbers', 'Prefer them and test call windows', 'Calls that connected on a primary number ended "No Pitch" %s; secondary %s; tertiary %s. 80%% of conversations happen before noon Pacific.' % tuple(['%.0f%%' % x[2] for x in C['slot'][:3]]) if len(C['slot']) >= 3 else 'n/a', A),
    ]
    tr = ''.join('<tr><td><b>%s</b><br><span class="note">%s</span></td><td>%s</td><td class="c">%s</td></tr>' % (e(a), e(b), e(c), v) for a, b, c, v in rows_sc)
    h.append('<section id="playbook"><h2>Checked against the Sales Blitz Playbook</h2><p class="lede">The playbook on thequantumleap.business sets the standards we sell. Here is how our own seat measures against each, using the same data as the rest of this page.</p>'
             '<div class="card"><table class="sc"><tr><th>Standard</th><th>Our numbers</th><th>Status</th></tr>%s</table></div>'
             '<div class="card" style="margin-top:14px"><h3>Fields the playbook says to capture, and where we are</h3><div class="two"><div><b class="good">Already captured on every call</b><p class="note">True outcome (stage reached), decision maker, opener quality, pitch made, objections and how they were handled, ask and confirmation, second of the ask, interest, next step.</p></div><div><b class="warn">Not yet captured</b><p class="note">Quick hang-up reason (opener, audio, caller ID, list, readiness), attempt count and last attempt date, rest-until date, employment verified on, target title tier, no-show recovery attempts.</p></div></div></div></section>' % tr)
    L = M['listen']; lk = lambda ids: ' '.join('<a href="https://app.hubspot.com/contacts/20682069/record/0-48/%s" target="_blank" rel="noopener">%s</a>' % (i, i) for i in ids)
    h.append('<section><h2>Calls worth listening to</h2><p class="lede">The playbook says to review recordings before acting on a quick-hang-up number. These are HubSpot call records (open them to hear the recording).</p>'
             '<div class="two"><div class="card"><h3>Hung up in the opener (Kenzie seat)</h3><p class="note">Listen to the first ten seconds: how quickly does the rep speak, is there a delay, is the audio clear?</p><p>%s</p></div>'
             '<div class="card"><h3>Pitch heard, no ask (Kenzie seat)</h3><p class="note">Where could the ask have gone in?</p><p>%s</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>Calls that booked a meeting</h3><p>%s</p></div></section>' % (lk(L['hang']), lk(L['missed']), lk(L['booked'])))
    h.append('<section><h2>The short version</h2><p class="lede">There is no single villain. The biggest leaks are how short the conversations are, which lists we call, and what is said at the ask.</p><div class="card"><ol class="fix" style="margin:0">'
             '<li><b>We are not using the dialing time we are assigned.</b> October: %.0f of %.0f hours on the dialer (%.0f%%), which is 0.24 meetings per hour against a playbook pass mark of 0.41.</li><li><b>Half of all conversations are over in 20 seconds, and the Kenzie seat keeps calling the same people who have already picked up.</b> Nothing under 40 seconds booked; once past 90 seconds, about 1 in 5 do. Lists of people we have met or sent proposals to book several times better than lists of people who have only picked up before. (See the section above.)</li><li><b>The meeting is almost never asked for on the Kenzie seat.</b> %d asks across %d calls (%.0f%%). %d calls got as far as the pitch; only %d of those included an ask. %.0f%% of calls never ask at all.</li>'
             '<li><b>When Patrick asks without closing language, it never books.</b> Plain asks: %d, booked %d. Asks that used an alternative or assumptive close ("mornings or afternoons?", "what if I sent an invite for 15 minutes?"): %d, booked %d. Every one of his %d bookings used one.</li>'
             '<li><b>The opener loses about 4 in 10 of the people we reach.</b> %.0f%% of live conversations on the Kenzie seat end in the opener, median call %d seconds (Patrick: %.0f%%, %d seconds).</li>'
             '<li><b>Objections are mostly not answered.</b> %.0f%% of objections on the Kenzie seat get no real response ("Not interested? Okay, then."). Patrick answers well on %.0f%%, and those calls book %d of %d times.</li></ol></div></section>' % (
                 DIAL['Oct']['on_dialer'], DIAL['Oct']['assigned'], pc(DIAL['Oct']['on_dialer'], DIAL['Oct']['assigned']), K['asks'], K['n'], pc(K['asks'], K['n']), kpitch, kask, pc(K['never'], K['n']),
                 Pt['asks_plain'], Pt['booked_plain'], Pt['asks_close'], Pt['booked_close'], Pt['booked_close'],
                 pc(K['hung'], K['live']), K['dur'], pc(Pt['hung'], Pt['live']), Pt['dur'],
                 pc(K['ob_not'], K['ob']), pc(Pt['ob_good'], Pt['ob']), 10, 22))
    h.append('<section><h2>The funnel, side by side</h2><p class="lede">Percentages are of all calls with a transcript for that rep. This is the AI read, so its booking counts (5 and 13) differ slightly from ConnectAndSell\'s own (6 and 13) for the same period.</p><div class="card">%s</div><div class="card"><h3>By week</h3><table><tr><th></th><th>Kenzie calls</th><th>reached a person</th><th>booked</th><th>Patrick calls</th><th>reached a person</th><th>booked</th></tr>%s</table><p class="note">The most recent week is partial.</p></div></section>' % (funnel_table(M), wk))
    h.append('<section><h2>Finding 1: the ask is missing</h2><p class="lede">Of the people who stay on the line through the pitch, almost none are asked for a meeting on the Kenzie seat.</p><div class="two"><div class="card"><h3>Kenzie seat: when the ask comes</h3>%s</div><div class="card"><h3>Patrick: when the ask comes</h3>%s</div></div></section>' % (
        bars([('Never asked', K['never']), ('Asked (any point)', K['asks'])], K['n'], 'var(--bad)'), bars([('Never asked', Pt['never']), ('Asked (any point)', Pt['asks'])], Pt['n'], 'var(--c3)')))
    h.append('<section><h2>Finding 2: only closing language books meetings</h2><p class="lede">Same rep, same kind of calls: what he says at the ask decides the result.</p><div class="two"><div class="card"><div class="big bad">0 of %d</div><p>plain asks booked (for example "would you be open to a call?").</p></div><div class="card"><div class="big good">%d of %d</div><p>asks with an alternative or assumptive close booked.</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>What the booking calls sound like (Patrick)</h3>'
             '<blockquote>"Would it make sense to just put a placeholder on the calendar in mid-November and then I could just follow up the week before and confirm the time?"<small>Assumptive close on a "not now" answer</small></blockquote>'
             '<blockquote>"Are mornings or afternoons typically better for you? ... You are central time, right? How about 10:00?"<small>Alternative close, then a specific time</small></blockquote>'
             '<blockquote>"What if I sent you an invite to connect for like 15 minutes and we could kind of talk through it then? Would that work?"<small>Small ask, then "how is 1:00 for you?"</small></blockquote>'
             '<p class="note">He uses a close on %d of his %d asks (%.0f%%) and on %.0f%% of all his calls. The Kenzie seat used one on %d of %d calls. Quotes are lightly cleaned from the transcripts.</p></div></section>' % (
                 Pt['asks_plain'], Pt['booked_close'], Pt['asks_close'], Pt['asks_close'], Pt['asks'], pc(Pt['asks_close'], Pt['asks']), pc(Pt['asks_close'], Pt['n']), K['asks_close'], K['n']))
    ob = lambda R: bars([(OBJ.get(k, k), v) for k, v in R['objs'].most_common(7)], sum(R['objs'].values()), 'var(--warn)')
    h.append('<section><h2>Finding 3: the opener and the objections</h2><p class="lede">The opener is where most of the transcribed conversations are lost.</p><div class="two"><div class="card"><h3>Where live conversations end (Kenzie seat)</h3>%s<p class="note">Hung up in the opener: %d. Refused right after: %d. Of %d people reached.</p></div>'
             '<div class="card"><h3>Opener quality (AI-scored)</h3>%s</div></div>'
             '<div class="card" style="margin-top:14px"><h3>What the opener sounds like</h3><blockquote>"I\'m calling with Quantum Business Solutions ... I know I\'m an interruption here, but mind if I grab half a minute to let you know why I called?" ... "we help companies improve their sales process through CRM solutions and lead generation."<small>Typical Kenzie-seat opener: polite, but generic. Nothing in it says why this person should stay on.</small></blockquote>'
             '<p>Openers that acknowledge the interruption are associated with fewer immediate hang-ups (%.0f%% vs %.0f%%), but this has to be read carefully: calls that end early never get to say the line, so it is a hint to test, not proof.</p></div>'
             '<div class="two" style="margin-top:14px"><div class="card"><h3>Objections raised (Kenzie seat)</h3>%s<p class="note">%d objections: %d not handled (%.0f%%), %d handled well.</p></div><div class="card"><h3>Objections raised (Patrick)</h3>%s<p class="note">%d objections: %d not handled (%.0f%%), %d handled well.</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>Typical missed recoveries</h3><blockquote>Prospect: "I am on a call right now, try me again next week." Rep: "Sure. Let me send you some information via email."<small>A call-back request turned into an email, with no time locked in.</small></blockquote>'
             '<blockquote>Prospect: "All right, I appreciate the call but no need for your services." Rep: "Not interested? Okay, then."<small>Ends the call at the first no.</small></blockquote></div></section>' % (
                 bars([('Hung up in the opener', K['hung']), ('Refused right after', K['refused']), ('Stayed past the opener', K['live'] - K['hung'] - K['refused'])], K['live'], 'var(--bad)'),
                 K['hung'], K['refused'], K['live'], bars([(k.replace('_', ' ').title(), v) for k, v in K['opener'].most_common()], K['n'], 'var(--c3)'),
                 M['interrupt']['a_hang'], M['interrupt']['b_hang'], ob(K), K['ob'], K['ob_not'], pc(K['ob_not'], K['ob']), K['ob_good'], ob(Pt), Pt['ob'], Pt['ob_not'], pc(Pt['ob_not'], Pt['ob']), Pt['ob_good']))
    dm = lambda R: R['dm']['yes']
    h.append('<section><h2>Finding 4: who we reach, and what happens after a booking</h2><p class="lede">List quality matters less than the call, but it is not nothing.</p><div class="two"><div class="card"><h3>Decision maker identified</h3><table><tr><th></th><th>Kenzie seat</th><th>Patrick</th></tr><tr><td>Yes</td><td class="n">%d</td><td class="n">%d</td></tr><tr><td>No</td><td class="n">%d</td><td class="n">%d</td></tr><tr><td>Never established</td><td class="n">%d</td><td class="n">%d</td></tr></table><p class="note">The decision maker is rarely established, so we do not know who we are talking to on most calls.</p></div>'
             '<div class="card"><h3>Bookings that stick</h3><div class="big warn">%d of %d</div><p>booked meetings have a confirmed invite. The rest rely on a prospect remembering a verbal agreement.</p></div></div></section>' % (
                 dm(K), dm(Pt), K['dm']['no'], Pt['dm']['no'], K['dm']['unclear'], Pt['dm']['unclear'], T['confirmed'], T['booked']))
    h.append('<section><h2>What to try, built from the calls that worked</h2><p class="lede">Drafts to test, not scripts to read word for word. Change one thing at a time and watch the numbers on this page.</p><div class="two">'
             '<div class="card"><h3>The ask (use on every conversation past the opener)</h3><blockquote>"The reason I am calling is to set up 15 minutes to talk through your sales and marketing priorities. Are mornings or afternoons usually better for you?"</blockquote><blockquote>"I will send a quick invite. Does Tuesday at 10 or Thursday at 2 work better?"</blockquote><p class="note">Both are the alternative-close pattern behind every booking in this data.</p></div>'
             '<div class="card"><h3>When they say "no time" or "call me back"</h3><blockquote>"Totally understand. That is exactly why I am asking for 15 minutes next week. Would Tuesday or Thursday be better?"</blockquote><p class="note">Today these are usually answered with "I will send you some information", which books nothing.</p></div>'
             '<div class="card"><h3>When they say "not interested"</h3><blockquote>"Fair enough. Can I ask what you are using today for your CRM? I will not take more than a minute."</blockquote><p class="note">One question before the call ends. Today the call usually ends at the first no.</p></div>'
             '<div class="card"><h3>The opener</h3><p>Start with something specific to them (their CRM, a recent change, a prior conversation) in the first sentence, then the permission line. Test two or three versions and compare the share that hang up in the opener (now %.0f%% on the Kenzie seat).</p></div></div></section>' % pc(K['hung'], K['live']))
    h.append('<section><h2>What to change, in order</h2><ol class="fix">'
             '<li><b>Spend the dialing time on people we know first.</b> Deal Follow-Up, All Time Meetings, Hot List and No-Shows book at about 8%% of conversations versus about 1%% on the picked-up-before lists, where the Kenzie seat spends almost all of its time.</li>'
             '<li><b>Make the ask mandatory on every call that gets past the opener.</b> Today it is under 5%% on the Kenzie seat and 42%% for Patrick. Target 50%%+ of conversations, with the ask coming right after the first reason they would care.</li>'
             '<li><b>Standardise the close.</b> One alternative close ("Tuesday at 10 or Thursday at 2?") and one assumptive close ("I will send an invite for 15 minutes, mornings or afternoons?"). Use it on every ask. In this data, plain asks booked 0 of %d across both reps.</li>'
             '<li><b>Rewrite and A/B test the opener.</b> Lead with a specific reason (their CRM, a recent change), not a category description. Track the share of calls that hang up in the opener (now %.0f%%) per version.</li>'
             '<li><b>Give the reps a one-line recovery for each top objection.</b> "No time" and "call back later" should end with a time on the calendar, not an email. "Not interested" gets one question before the call ends.</li>'
             '<li><b>Confirm the invite on the call.</b> Read the email address back, send the invite while on the phone, and ask them to accept it. Only %d of %d bookings are confirmed.</li>'
             '<li><b>Fix who is on the other end.</b> Establish the decision maker early, and when it is someone else, ask for a warm transfer or the right name instead of settling for an email address.</li></ol></section>' % (
                 Pt['asks_plain'] + K['asks_plain'], pc(K['hung'], K['live']), T['confirmed'], T['booked']))
    h.append('<section><h2>How this was measured</h2><div class="card"><p>Every call since %s with a ConnectAndSell transcript in HubSpot, scored by an AI reading the full transcript for the stage reached, the opener, whether and how a meeting was asked for, the objections and how they were handled. "Booked" means the call reached a meeting agreed, a time set or an invite confirmed. Parts of many transcripts are masked for dual-consent reasons, so the prospect side is incomplete. The Kenzie seat is the HubSpot call owner; the transcripts label the caller with that seat\'s name, but the caller introduces themselves with other first names on some calls, which is worth confirming. Percentages are shares of calls, not of people.</p></div></section></main></body></html>' % s)
    ia = next(i for i, s_ in enumerate(h) if s_.startswith('<section><h2>What ConnectAndSell itself shows'))
    ib = next(i for i, s_ in enumerate(h) if s_.startswith('<section><h2>The short version'))
    if ia < ib: h.insert(ia, h.pop(ib))
    il = next(i for i, s_ in enumerate(h) if s_.startswith('<section id="lost">'))
    h.insert(next(i for i, s_ in enumerate(h) if s_.startswith('<section')), h.pop(il))
    return ''.join(h)


if __name__ == '__main__':
    since = sys.argv[sys.argv.index('--since') + 1] if '--since' in sys.argv else '2026-09-28'
    D = load(since); M = metrics(D); C = cas_metrics(since); doc = page(M, since, C)
    open('/tmp/meetings_page.html', 'w').write(doc)
    print('calls', len(D), '| booked', M['total']['booked'], '| html', len(doc), '-> /tmp/meetings_page.html')
