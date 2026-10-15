#!/usr/bin/env python3
"""Call Intel weekly run - processes only the last N days of calls (default 7).

  python3 weekly.py            # dry run: reports what it would do, writes nothing to HubSpot
  python3 weekly.py --apply    # does it

Steps: (1) sync dialer transcripts to call records, (2) score new calls (transcript -> hybrid; notes/summary -> signals only),
       (3) roll up to the companies those calls touch + tasks for buying signals, (4) refresh the stats JSON for the Call Analysis page.
"""
import argparse, datetime, json, os, sys, time, concurrent.futures as cf
from clients import hs
import cas_sync, scoring, rollup, contacts, stats, props

ap = argparse.ArgumentParser()
ap.add_argument('--days', type=int, default=7)
ap.add_argument('--apply', action='store_true')
ap.add_argument('--skip-sync', action='store_true')
ap.add_argument('--skip-stats', action='store_true')
ap.add_argument('--out', default='call_intel_stats.json')
a = ap.parse_args()
APPLY = a.apply
today = datetime.date.today()
d_from, d_to = today - datetime.timedelta(days=a.days), today
report = {'window': '%s..%s' % (d_from, d_to), 'apply': APPLY}
print('Call Intel weekly', report, flush=True)


def ms(d): return str(int(datetime.datetime.combine(d, datetime.time()).replace(tzinfo=datetime.timezone.utc).timestamp() * 1000))


# 1 transcripts ---------------------------------------------------------------------------------
synced = {}
if not a.skip_sync:
    st, synced = cas_sync.sync(d_from - datetime.timedelta(days=1), d_to, apply=APPLY)
    report['transcript_sync'] = st; print('sync', st, flush=True)

# 2 find the window's calls that Call Intel has not processed ----------------------------------
FIELDS = ['hs_timestamp', 'call_intel', 'ai__signal_source', props.TRANSCRIPT, 'hs_call_summary', 'hs_ai_summary', 'hs_call_transcript_tracked_terms', 'hs_call_body']
ids, after = [], 0
while True:     # search only lists the week's call ids (timestamps are indexed long ago); properties are then READ, which is always current
    r = hs('POST', '/crm/v3/objects/calls/search', {'filterGroups': [{'filters': [
        {'propertyName': 'hs_timestamp', 'operator': 'GTE', 'value': ms(d_from - datetime.timedelta(days=1))},
        {'propertyName': 'hs_timestamp', 'operator': 'LT', 'value': ms(d_to + datetime.timedelta(days=1))}]}], 'limit': 100, 'after': after, 'properties': ['hs_timestamp']})
    ids += [x['id'] for x in r['results']]; nx = (r.get('paging') or {}).get('next', {}).get('after')
    if not nx or int(nx) >= 9900: break
    after = nx
calls = []
for i in range(0, len(ids), 100):
    calls += [c for c in hs('POST', '/crm/v3/objects/calls/batch/read', {'properties': FIELDS, 'inputs': [{'id': x} for x in ids[i:i + 100]]})['results']
              if c['properties'].get('call_intel') != 'true'
              or (c['properties'].get('ai__signal_source') == 'call_summary' and len(c['properties'].get(props.TRANSCRIPT) or '') >= 40)]   # upgrade notes-only calls once a transcript exists
tx = [c for c in calls if len(c['properties'].get(props.TRANSCRIPT) or '') >= 40]
have = {c['id'] for c in tx}
notes = [c for c in calls if c['id'] not in have and len(scoring.notes_text(c['properties'])) >= 40]
report['calls_in_window_unprocessed'] = len(calls); report['with_transcript'] = len(tx); report['notes_only'] = len(notes)
print('to score: %d transcripts, %d notes-only (of %d unprocessed calls)' % (len(tx), len(notes), len(calls)), flush=True)


def work(item):
    kind, c = item; p = c['properties']; date = p['hs_timestamp'][:10]
    if kind == 'tx':
        pr, m = scoring.score_transcript(p[props.TRANSCRIPT], date)
    else:
        pr, m = scoring.score_notes(scoring.notes_text(p), date)
    return c['id'], pr


scored, failed, buf = [], 0, []
if APPLY or True:
    with cf.ThreadPoolExecutor(12) as ex:
        for cid, pr in ex.map(work, [('tx', c) for c in tx] + [('notes', c) for c in notes]):
            if pr is None: failed += 1; continue
            scored.append(cid)
            if APPLY:
                buf.append({'id': cid, 'properties': pr})
                if len(buf) >= 50: hs('POST', '/crm/v3/objects/calls/batch/update', {'inputs': buf}); buf = []
    if APPLY and buf: hs('POST', '/crm/v3/objects/calls/batch/update', {'inputs': buf})
report['scored'] = len(scored); report['score_failures'] = failed
print('scored', len(scored), 'failed', failed, flush=True)

# 3 roll up the companies those calls touch ---------------------------------------------------
companies = set()
for i in range(0, len(scored), 100):
    b = hs('POST', '/crm/v4/associations/calls/companies/batch/read', {'inputs': [{'id': c} for c in scored[i:i + 100]]})
    for r in b.get('results', []):
        for x in r['to']: companies.add(str(x['toObjectId']))
if APPLY and companies:
    time.sleep(5)    # let HubSpot index the new call properties
    report['rollup'] = rollup.run(companies, apply=True)
else:
    report['rollup'] = {'companies_touched': len(companies), 'note': 'dry run - roll-up not applied'}
print('rollup', report['rollup'], flush=True)

# 3b contacts those calls involve, and the weekly refresh of the 'contract window' dropdowns the lists use ---------------
people = set()
for i in range(0, len(scored), 100):
    b = hs('POST', '/crm/v4/associations/calls/contacts/batch/read', {'inputs': [{'id': c} for c in scored[i:i + 100]]})
    for r in b.get('results', []):
        for x in r['to']: people.add(str(x['toObjectId']))
if APPLY:
    report['contacts'] = contacts.run(people, apply=True)
    report['contract_windows'] = rollup.refresh_contract_windows(apply=True)
else:
    report['contacts'] = {'contacts_touched': len(people), 'note': 'dry run'}
print('contacts', report['contacts'], report.get('contract_windows'), flush=True)


# 4 stats for the Call Analysis page ---------------------------------------------------------
if not a.skip_stats:
    owners = {o['id']: ('%s %s' % (o.get('firstName') or '', o.get('lastName') or '')).strip()
              for o in hs('GET', '/crm/v3/owners?limit=500').get('results', [])}
    s = stats.build(owner_names=owners); json.dump(s, open(a.out, 'w'))
    if APPLY and os.environ.get('CLIENTCOMMAND_URL'):
        import publish
        report['page'] = publish.publish(s, apply=True); print('page', report['page'], flush=True)
    report['stats_file'] = a.out; print('stats written', a.out, flush=True)
print('SUMMARY ' + json.dumps(report))
