"""Publish the 'Call Intel' section into the ClientCommand Call Analysis page.

Reads the page's current HTML through ClientCommand's MCP endpoint (env CLIENTCOMMAND_URL), replaces the block between the
CALL-INTEL markers (or inserts it before the data section the first time), and writes the page back. Totals and percentages only.
"""
import json, os, html, re, ssl, urllib.request
from clients import CTX, hs

PROPOSAL_ID = os.environ.get('CI_PAGE_PROPOSAL_ID', '7b447e84-1ea0-41a0-abcd-b1e6518f6410')
START, END = '<!-- CALL-INTEL:START -->', '<!-- CALL-INTEL:END -->'
STAGES = [('s01_no_live_answer', 'No live answer'), ('s02_gatekeeper', 'Stopped at gatekeeper'), ('s03_hung_up_in_opener', 'Hung up in the opener'),
          ('s04_refused_to_listen', 'Refused right after opener'), ('s05_pitch_given', 'Heard the pitch, disengaged'), ('s06_discovery', 'Real conversation'),
          ('s07_objection_unhandled', 'Objection, not overcome'), ('s08_objection_overcome', 'Objection overcome, no ask'),
          ('s09_meeting_asked_declined', 'Meeting asked, declined'), ('s10_meeting_agreed', 'Meeting agreed'), ('s11_time_set', 'Date and time set'),
          ('s12_invite_confirmed', 'Invite confirmed')]
ASK = [('a1_in_opener', 'In the opener'), ('a2_after_pitch', 'Right after the pitch'), ('a3_after_discovery', 'After discovery'),
       ('a4_after_objection', 'After an objection'), ('a5_late_or_rushed', 'Late or rushed'), ('a6_never_asked', 'Never asked')]
OBJ = {'not_interested': 'Not interested', 'no_time': 'No time', 'call_back_later': 'Call back later', 'not_decision_maker': 'Not the decision maker',
       'already_have_vendor': 'Already have a vendor', 'send_info': 'Send info', 'take_me_off_list': 'Take me off the list', 'no_budget': 'No budget',
       'gatekeeper': 'Gatekeeper', 'other': 'Other'}
VEND = {'crm': 'CRM', 'marketing_agency': 'Marketing agency', 'seo_agency': 'SEO/AEO agency', 'data_tool': 'Data tool', 'dialer': 'Dialer',
        'appt_setting': 'Appointment setting', 'equipment_lease': 'Equipment lease'}


def _bars(pairs, total, color='var(--accent)'):
    rows = []
    for label, n in pairs:
        pct = 100 * n / total if total else 0
        rows.append('<div style="display:grid;grid-template-columns:minmax(120px,190px) minmax(60px,1fr) 96px;gap:10px;align-items:center;margin:5px 0;font-size:13px">'
                    '<span>%s</span><span style="background:var(--line2);border-radius:4px;height:14px;display:block">'
                    '<span style="display:block;height:14px;border-radius:4px;background:%s;width:%.1f%%"></span></span>'
                    '<span style="text-align:right;color:var(--mute);white-space:nowrap">%d &middot; %.1f%%</span></div>' % (html.escape(label), color, pct, n, pct))
    return ''.join(rows)


def _table(head, rows):
    h = ''.join('<th style="text-align:left;padding:4px 10px 4px 0;color:var(--mute);font-weight:600">%s</th>' % html.escape(x) for x in head)
    b = ''.join('<tr>' + ''.join('<td style="padding:4px 10px 4px 0;border-top:1px solid var(--line2)">%s</td>' % html.escape(str(c)) for c in r) + '</tr>' for r in rows)
    return '<table style="border-collapse:collapse;font-size:13px;width:100%%;table-layout:auto"><tr>%s</tr>%s</table>' % (h, b)


def section_html(s):
    a, w, co = s['all_time'], s['last_7_days'], s['companies']
    n = a['calls_scored']; r = a['rates']
    stage = a['stage']; top = max(stage, key=stage.get) if stage else ''
    lab = dict(STAGES)
    lede = ('%s conversations (calls that reached a person and have a transcript) have been read end to end. The biggest single stopping point is "%s" (%.0f%% of calls). A meeting was asked for on %s%% of calls, '
            'an alternative close was used on %s%% and an assumptive close on %s%%; %s%% of calls reached a booked meeting.' % (
                format(n, ','), lab.get(top, top), 100 * stage.get(top, 0) / n if n else 0, r['asked_for_meeting_pct'], r['alternative_close_pct'],
                r['assumptive_close_pct'], r['booked_pct']))
    wk = w['rates']
    c = []
    c.append('<div class="card"><h3>Where conversations end (calls that reached a person and have a transcript)</h3>%s</div>' % _bars([(l, stage.get(k, 0)) for k, l in STAGES], n))
    ask = a['ask_stage']; at = sum(ask.values())
    c.append('<div class="card"><h3>When the meeting ask comes</h3>%s</div>' % _bars([(l, ask.get(k, 0)) for k, l in ASK], at, 'var(--c3)'))
    ob = a['objections']; ot = sum(ob.values())
    c.append('<div class="card"><h3>Objections raised</h3>%s</div>' % _bars([(OBJ.get(k, k), v) for k, v in list(ob.items())[:10]], max(ot, 1), 'var(--warn)'))
    c.append('<div class="card"><h3>This week vs all time</h3>%s</div>' % _table(['Measure', 'Last 7 days', 'All time'], [
        ['Calls scored', w['calls_scored'], n], ['Asked for a meeting', '%s%%' % wk['asked_for_meeting_pct'], '%s%%' % r['asked_for_meeting_pct']],
        ['Alternative close used', '%s%%' % wk['alternative_close_pct'], '%s%%' % r['alternative_close_pct']],
        ['Assumptive close used', '%s%%' % wk['assumptive_close_pct'], '%s%%' % r['assumptive_close_pct']],
        ['Reached a booked meeting', '%s%%' % wk['booked_pct'], '%s%%' % r['booked_pct']],
        ['Invite confirmed (of booked)', '%s%%' % wk['invite_confirmed_of_booked_pct'], '%s%%' % r['invite_confirmed_of_booked_pct']]]))
    reps = s.get('reps_last_90_days') or {}
    if reps:
        c.append('<div class="card"><h3>By caller, last 90 days (30+ scored calls)</h3>%s</div>' % _table(['Caller', 'Calls', 'Asked', 'Alt. close', 'Assumptive', 'Booked'],
                 [[k, v['calls_scored'], '%s%%' % v['asked_for_meeting_pct'], '%s%%' % v['alternative_close_pct'], '%s%%' % v['assumptive_close_pct'], '%s%%' % v['booked_pct']] for k, v in sorted(reps.items(), key=lambda x: -x[1]['calls_scored'])]))
    hsx = co['hubspot_status']
    c.append('<div class="card"><h3>What prospects say about HubSpot (%s companies with signals)</h3>%s<p style="font-size:12px;color:var(--mute)">"Active" needs the prospect\'s own words; a rep saying it is counted as unconfirmed.</p></div>' % (
        format(co['with_signals'], ','), _bars([(k.title(), hsx.get(k, 0)) for k in ('active', 'unconfirmed', 'never', 'churned', 'considering') if k in hsx], max(sum(hsx.values()), 1), 'var(--c4)')))
    c.append('<div class="card"><h3>CRM and data tools mentioned</h3><div class="row" style="display:grid;grid-template-columns:1fr 1fr;gap:18px">%s%s</div></div>' % (
        _table(['CRM', 'Companies'], list(co['crm_top'].items())[:8]), _table(['Data tool', 'Companies'], list(co['data_tool_top'].items())[:6])))
    soon = co['contracts_ending_next_90_days']
    c.append('<div class="card"><h3>Contracts ending in the next 90 days</h3>%s</div>' % _table(['Vendor', 'Companies'], [[VEND[k], v] for k, v in soon.items()]))
    body = ''.join('<div class="row">%s</div>' % x for x in c)
    return (START + '<section id="callintel"><h2>Call Intel: what the call transcripts tell us (updated %s)</h2><p class="lede">%s</p>%s'
            '<p style="font-size:12px;color:var(--mute)">Totals and percentages only. Refreshed every Monday from the last week of calls; scores come from the call transcripts.</p></section>' % (
                html.escape(s['generated']), html.escape(lede), body) + END)


# ---- ClientCommand MCP endpoint (HTTP JSON-RPC) ----
def _rpc(method, params):
    req = urllib.request.Request(os.environ['CLIENTCOMMAND_URL'], json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, method='POST')
    raw = urllib.request.urlopen(req, context=CTX, timeout=300).read().decode()
    if raw.lstrip().startswith('event') or 'data:' in raw[:20]:
        raw = [l[5:].strip() for l in raw.splitlines() if l.startswith('data:')][-1]
    return json.loads(raw)


def _tool(name, args):
    r = _rpc('tools/call', {'name': name, 'arguments': args})
    if r.get('error'): raise RuntimeError(r['error'])
    return json.loads(r['result']['content'][0]['text'])


def merge(page_html, section):
    if START in page_html and END in page_html:
        return re.sub(re.escape(START) + '.*?' + re.escape(END), lambda m: section, page_html, flags=re.S)
    page_html = page_html.replace('<section id="data">', section + '<section id="data">', 1) if '<section id="data">' in page_html else page_html.replace('</body>', section + '</body>', 1)
    if 'href="#callintel"' not in page_html:
        page_html = page_html.replace('<small style="margin-top:14px">Next</small>', '<small style="margin-top:14px">Call Intel</small><a href="#callintel">Call Intel (weekly)</a><small style="margin-top:14px">Next</small>', 1)
    return page_html


def publish(stats, apply=True):
    page = _tool('get_web_proposal', {'proposalId': PROPOSAL_ID})['custom_html']
    new = merge(page, section_html(stats))
    if apply: _tool('set_web_proposal_custom_html', {'proposal_id': PROPOSAL_ID, 'html': new})
    return {'page_chars_before': len(page), 'page_chars_after': len(new), 'published': apply}


if __name__ == '__main__':
    import sys
    s = json.load(open(sys.argv[1]))
    if '--preview' in sys.argv:
        open('/tmp/callintel_section_preview.html', 'w').write('<!doctype html><meta charset=utf-8><body style="font-family:sans-serif;max-width:900px;margin:20px auto">' + section_html(s))
        print('preview written')
    else:
        print(publish(s, apply='--apply' in sys.argv))
