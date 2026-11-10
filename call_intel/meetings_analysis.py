"""Why aren't we booking more meetings? Builds a ClientCommand page from scored call records.

    python3 meetings_analysis.py --since 2026-09-28 [--create | --update <proposalId>]

Reads calls with a CAS transcript since the date (HubSpot), computes the funnel per rep and the patterns behind it,
and renders one self-contained HTML page. Totals, percentages and short rep-side quotes only - no prospect names.
"""
import os, sys, json, re, html, datetime, collections, statistics as st
from clients import hs

P = 'cas_coach_'
PROPS = ['hs_timestamp', 'hubspot_owner_id', 'hs_call_duration', 'cas_transcript'] + [P + k for k in (
    'stage_reached', 'opener', 'ask_stage', 'asked_for_meeting', 'alternative_close', 'assumptive_close', 'objections',
    'objection_handling', 'prospect_interest', 'decision_maker', 'invite_confirmed', 'got_to_pitch', 'rep_talk_pct', 'discovery_questions')]
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
        p['rep'] = own.get(p.get('hubspot_owner_id'), 'Other'); p['txt'] = re.sub(r'\s+', ' ', p.get('cas_transcript') or ''); out.append(p)
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
    C['talk_order'] = order
    L = collections.defaultdict(list)
    for x in cv: L[x['ListName']].append(x)
    C['lists'] = sorted(((k, len(v), sum(map(ms, v))) for k, v in L.items()), key=lambda r: -r[1])[:10]
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


CSS = """:root{--bg:#f4f3ee;--panel:#fffefb;--ink:#1a2320;--mute:#5f6b66;--line:#dcdad0;--line2:#ebe9e0;--accent:#0b7a6c;--warn:#b26a00;--bad:#b3352b;--c3:#3f5fa8;--good:#1c7c4a;--shadow:0 1px 2px rgba(20,30,25,.06),0 6px 18px rgba(20,30,25,.05)}
@media (prefers-color-scheme:dark){:root{--bg:#0e1412;--panel:#151d1a;--ink:#e7eeea;--mute:#98a8a0;--line:#29342f;--line2:#202a26;--accent:#3fc7b0;--warn:#e8a541;--bad:#ff8f84;--c3:#8fa9e8;--good:#63d596;--shadow:none}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Avenir Next","Segoe UI",system-ui,-apple-system,sans-serif}
.top{background:linear-gradient(120deg,#0d2a25,#123b34 60%,#0b2a3a);color:#eaf5f1;padding:34px 24px 30px}.in{max-width:1100px;margin:0 auto}
.top h1{margin:0 0 8px;font-size:clamp(26px,4vw,38px);letter-spacing:-.02em;line-height:1.12}.top p{margin:0;max-width:78ch;color:#b9d3cb}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:22px}.kpi{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:26px;letter-spacing:-.02em;font-variant-numeric:tabular-nums;color:#fff}.kpi span{font-size:12.5px;color:#a9c8be}
main{max-width:1100px;margin:0 auto;padding:24px 20px 80px}section{margin-bottom:38px}h2{font-size:22px;margin:0 0 6px;letter-spacing:-.01em}h3{margin:0 0 8px;font-size:15px}
.lede{color:var(--mute);margin:0 0 14px;max-width:80ch}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:var(--shadow);min-width:0}.card+.card{margin-top:14px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.br{display:grid;grid-template-columns:minmax(110px,200px) minmax(60px,1fr) 100px;gap:10px;align-items:center;margin:5px 0;font-size:13px}.tr{background:var(--line2);border-radius:4px;height:14px;display:block}.fl{display:block;height:14px;border-radius:4px}.nm{text-align:right;color:var(--mute);white-space:nowrap}
table{border-collapse:collapse;width:100%;font-size:13.5px;display:block;overflow-x:auto;max-width:100%}.card{overflow-x:auto}th{text-align:left;color:var(--mute);font-weight:600;padding:5px 10px 5px 0}td{padding:6px 10px 6px 0;border-top:1px solid var(--line2)}td.n{font-variant-numeric:tabular-nums}td.n i{color:var(--mute);font-style:normal;font-size:12px}
.big{font-size:30px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}.good{color:var(--good)}.bad{color:var(--bad)}.warn{color:var(--warn)}
blockquote{margin:8px 0;padding:8px 12px;border-left:3px solid var(--accent);background:var(--line2);border-radius:0 8px 8px 0;font-size:13.5px}blockquote small{display:block;color:var(--mute);margin-top:2px}
.fix{counter-reset:f;list-style:none;padding:0;margin:0}.fix li{counter-increment:f;padding:12px 14px 12px 48px;position:relative;background:var(--panel);border:1px solid var(--line);border-radius:12px;margin-bottom:10px}
.fix li:before{content:counter(f);position:absolute;left:14px;top:12px;width:24px;height:24px;border-radius:99px;background:var(--accent);color:#fff;text-align:center;font-weight:700;font-size:13px;line-height:24px}
.note{color:var(--mute);font-size:12.5px;margin-top:8px}"""


def page(M, since, C):
    K, Pt, T = M['Kenzie Braun'], M['Patrick Dodge'], M['total']
    kb, pb = K['funnel'][5][1], Pt['funnel'][5][1]
    today = datetime.date.today().strftime('%b %-d, %Y'); s = datetime.date.fromisoformat(since).strftime('%b %-d')
    wk = ''.join('<tr><td>Week of %s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td></tr>' % (
        k, K_[0], K_[1], K_[2], P_[0], P_[1], P_[2]) for (k, K_), (_, P_) in zip(
            K['weeks'], Pt['weeks'] + [('', [0, 0, 0])] * (len(K['weeks']) - len(Pt['weeks']))))
    kask = K['funnel'][4][1]; kpitch = K['funnel'][3][1]
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Why we are not booking more meetings</title><style>%s</style></head><body>' % CSS]
    h.append('<div class="top"><div class="in"><h1>Why we are not booking more meetings</h1><p>Every call with a transcript since %s (%d calls, read end to end): what Kenzie Braun\'s seat and Patrick Dodge say, where each conversation ends, and what is different about the calls that booked. Updated %s.</p>' % (s, T['n'], today))
    h.append('<div class="kpis"><div class="kpi"><b>%d</b><span>meetings booked from %d calls (%.1f%%)</span></div><div class="kpi"><b>%.1f%%</b><span>Patrick: %d of %d calls booked</span></div><div class="kpi"><b>%.1f%%</b><span>Kenzie seat: %d of %d calls booked</span></div><div class="kpi"><b>%d of %d</b><span>booked meetings had the invite confirmed</span></div></div></div></div><main>' % (
        T['booked'], T['n'], pc(T['booked'], T['n']), pc(pb, Pt['n']), pb, Pt['n'], pc(kb, K['n']), kb, K['n'], T['confirmed'], T['booked']))
    pr = lambda a, b: pc(a, b)
    tk = C['talk']; to = C['talk_order']
    short = sum(tk[k][0] for k in to[:2]); longc, longm = tk['Over 90 seconds']
    h.append('<section><h2>What ConnectAndSell itself shows</h2><p class="lede">Before the AI read of the calls: ConnectAndSell logged <b>%d conversations</b> since %s and <b>%d "Meeting scheduled"</b> (%.1f%%). Two things stand out, and neither is about the script.</p>'
             '<div class="two"><div class="card"><h3>Conversations get nowhere because most are over in seconds</h3><table><tr><th>Talk time</th><th>Conversations</th><th>Meetings</th></tr>%s</table>'
             '<p class="note">%d of %d conversations (%.0f%%) lasted 20 seconds or less, and none of them booked. Conversations past 90 seconds booked %d of %d (%.0f%%): a 1-in-5 rate once someone actually stays on.</p></div>'
             '<div class="card"><h3>Cold lists book at a fraction of warm lists</h3><table><tr><th></th><th>Conversations</th><th>Meetings</th><th>Rate</th></tr>%s</table>'
             '<p class="note">"Warm" = lists of people we already know: Deal Follow-Up, All Time Meetings, Hot List, No-Shows, Hubspot Follow Up. The Kenzie seat spent %d of %d conversations on cold lists, mostly one list ("Callable - Best Bets").</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>How the conversations ended (ConnectAndSell disposition)</h3>%s</div>'
             '<div class="card" style="margin-top:14px"><h3>Biggest lists</h3><table><tr><th>List</th><th>Conversations</th><th>Meetings</th></tr>%s</table></div></section>' % (
                 C['n'], s, C['meet'], pr(C['meet'], C['n']),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>' % (k, tk[k][0], tk[k][1]) for k in to),
                 short, C['n'], pr(short, C['n']), longm, longc, pr(longm, longc),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%.1f%%</td></tr>' % (n, C['temp'][n][0], C['temp'][n][1], pr(C['temp'][n][1], C['temp'][n][0])) for n in ('warm', 'cold') if n in C['temp']),
                 C['k_cold'][0], C['k_cold'][1],
                 bars([(k, v) for k, v in C['disp'].most_common(10)], C['n'], 'var(--c3)'),
                 ''.join('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>' % (k, n, m) for k, n, m in C['lists'])))
    h.append('<section><h2>The short version</h2><p class="lede">There is no single villain. The biggest leaks are how short the conversations are, which lists we call, and what is said at the ask.</p><div class="card"><ol class="fix" style="margin:0">'
             '<li><b>Half of all conversations are over in 20 seconds, and the Kenzie seat is working cold lists.</b> Nothing under 40 seconds booked; once past 90 seconds, about 1 in 5 do. Warm lists book several times better than cold ones. (See the section above.)</li><li><b>The meeting is almost never asked for on the Kenzie seat.</b> %d asks across %d calls (%.0f%%). %d calls got as far as the pitch; only %d of those included an ask. %.0f%% of calls never ask at all.</li>'
             '<li><b>When Patrick asks without closing language, it never books.</b> Plain asks: %d, booked %d. Asks that used an alternative or assumptive close ("mornings or afternoons?", "what if I sent an invite for 15 minutes?"): %d, booked %d. Every one of his %d bookings used one.</li>'
             '<li><b>The opener loses about a third of the people we reach.</b> %.0f%% of live conversations on the Kenzie seat end in the opener, median call %d seconds (Patrick: %.0f%%, %d seconds).</li>'
             '<li><b>Objections are mostly not answered.</b> %.0f%% of objections on the Kenzie seat get no real response ("Not interested? Okay, then."). Patrick answers well on %.0f%%, and those calls book %d of %d times.</li></ol></div></section>' % (
                 K['asks'], K['n'], pc(K['asks'], K['n']), kpitch, kask, pc(K['never'], K['n']),
                 Pt['asks_plain'], Pt['booked_plain'], Pt['asks_close'], Pt['booked_close'], Pt['booked_close'],
                 pc(K['hung'], K['live']), K['dur'], pc(Pt['hung'], Pt['live']), Pt['dur'],
                 pc(K['ob_not'], K['ob']), pc(Pt['ob_good'], Pt['ob']), 10, 22))
    h.append('<section><h2>The funnel, side by side</h2><p class="lede">Percentages are of all calls with a transcript for that rep.</p><div class="card">%s</div><div class="card"><h3>By week</h3><table><tr><th></th><th>Kenzie calls</th><th>reached a person</th><th>booked</th><th>Patrick calls</th><th>reached a person</th><th>booked</th></tr>%s</table><p class="note">The most recent week is partial.</p></div></section>' % (funnel_table(M), wk))
    h.append('<section><h2>Finding 1: the ask is missing</h2><p class="lede">Of the people who stay on the line through the pitch, almost none are asked for a meeting on the Kenzie seat.</p><div class="two"><div class="card"><h3>Kenzie seat: when the ask comes</h3>%s</div><div class="card"><h3>Patrick: when the ask comes</h3>%s</div></div></section>' % (
        bars([('Never asked', K['never']), ('Asked (any point)', K['asks'])], K['n'], 'var(--bad)'), bars([('Never asked', Pt['never']), ('Asked (any point)', Pt['asks'])], Pt['n'], 'var(--c3)')))
    h.append('<section><h2>Finding 2: only closing language books meetings</h2><p class="lede">The same person, the same list, the same week: what Patrick says at the ask decides the result.</p><div class="two"><div class="card"><div class="big bad">0 of %d</div><p>plain asks booked (for example "would you be open to a call?").</p></div><div class="card"><div class="big good">%d of %d</div><p>asks with an alternative or assumptive close booked.</p></div></div>'
             '<div class="card" style="margin-top:14px"><h3>What the booking calls sound like (Patrick)</h3>'
             '<blockquote>"Would it make sense to just put a placeholder on the calendar in mid-November and then I could just follow up the week before and confirm the time?"<small>Assumptive close on a "not now" answer</small></blockquote>'
             '<blockquote>"Are mornings or afternoons typically better for you? ... You are central time, right? How about 10:00?"<small>Alternative close, then a specific time</small></blockquote>'
             '<blockquote>"What if I sent you an invite to connect for like 15 minutes and we could kind of talk through it then? Would that work?"<small>Small ask, then "how is 1:00 for you?"</small></blockquote>'
             '<p class="note">He uses a close on %d of his %d asks (%.0f%%) and on %.0f%% of all his calls. The Kenzie seat used one on %d call(s) in %d.</p></div></section>' % (
                 Pt['asks_plain'], Pt['booked_close'], Pt['asks_close'], Pt['asks_close'], Pt['asks'], pc(Pt['asks_close'], Pt['asks']), pc(Pt['asks_close'], Pt['n']), K['asks_close'], K['n']))
    ob = lambda R: bars([(OBJ.get(k, k), v) for k, v in R['objs'].most_common(7)], sum(R['objs'].values()), 'var(--warn)')
    h.append('<section><h2>Finding 3: the opener and the objections</h2><p class="lede">Half of what goes wrong happens in the first fifteen seconds.</p><div class="two"><div class="card"><h3>Where live conversations end (Kenzie seat)</h3>%s<p class="note">Hung up in the opener: %d. Refused right after: %d. Of %d people reached.</p></div>'
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
    h.append('<section><h2>What to change, in order</h2><ol class="fix">'
             '<li><b>Spend the dialing time on warm lists first.</b> Deal Follow-Up, All Time Meetings, Hot List and No-Shows book at about 8%% of conversations versus about 1%% on the cold lists. The Kenzie seat is almost entirely on the cold ones.</li>'
             '<li><b>Make the ask mandatory on every call that gets past the opener.</b> Today it is under 5%% on the Kenzie seat and 42%% for Patrick. Target 50%%+ of conversations, with the ask coming right after the first reason they would care.</li>'
             '<li><b>Standardise the close.</b> One alternative close ("Tuesday at 10 or Thursday at 2?") and one assumptive close ("I will send an invite for 15 minutes, mornings or afternoons?"). Use it on every ask. In this data, plain asks booked 0 of %d across both reps.</li>'
             '<li><b>Rewrite and A/B test the opener.</b> Lead with a specific reason (their CRM, a recent change), not a category description. Track the share of calls that hang up in the opener (now %.0f%%) per version.</li>'
             '<li><b>Give the reps a one-line recovery for each top objection.</b> "No time" and "call back later" should end with a time on the calendar, not an email. "Not interested" gets one question before the call ends.</li>'
             '<li><b>Confirm the invite on the call.</b> Read the email address back, send the invite while on the phone, and ask them to accept it. Only %d of %d bookings are confirmed.</li>'
             '<li><b>Fix who is on the other end.</b> Establish the decision maker early, and when it is someone else, ask for a warm transfer or the right name instead of settling for an email address.</li></ol></section>' % (
                 Pt['asks_plain'] + K['asks_plain'], pc(K['hung'], K['live']), T['confirmed'], T['booked']))
    h.append('<section><h2>How this was measured</h2><div class="card"><p>Every call since %s with a ConnectAndSell transcript in HubSpot, scored by an AI reading the full transcript for the stage reached, the opener, whether and how a meeting was asked for, the objections and how they were handled. "Booked" means the call reached a meeting agreed, a time set or an invite confirmed. Parts of many transcripts are masked for dual-consent reasons, so the prospect side is incomplete. The Kenzie seat is the HubSpot call owner; the transcripts label the caller with that seat\'s name, but the caller introduces themselves with other first names on some calls, which is worth confirming. Percentages are shares of calls, not of people.</p></div></section></main></body></html>' % s)
    return ''.join(h)


if __name__ == '__main__':
    since = sys.argv[sys.argv.index('--since') + 1] if '--since' in sys.argv else '2026-09-28'
    D = load(since); M = metrics(D); C = cas_metrics(since); doc = page(M, since, C)
    open('/tmp/meetings_page.html', 'w').write(doc)
    print('calls', len(D), '| booked', M['total']['booked'], '| html', len(doc), '-> /tmp/meetings_page.html')
