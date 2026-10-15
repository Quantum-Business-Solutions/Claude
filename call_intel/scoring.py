"""Hybrid scoring: Jev for typed facts (confidence-routed) + one LLM call for text/judgment fields."""
import re, datetime, concurrent.futures as cf
from clients import gemini, jev
import prompts, props

BOILERPLATE = re.compile(r'ConnectAndSell Agent Attempt.*?(<br>)?\s*Agent Disposition:[^\n<]*', re.I)


def _decisive(p): return p >= 0.8 or p <= 0.2


def _merge_jev(sig, co, a):
    """Override the LLM's answer with Jev's only where Jev is decisive. Returns number of overrides."""
    if not a: return 0
    n = 0
    for k in ('asked_for_meeting', 'alternative_close', 'assumptive_close'):
        p = a[k]['noul']
        if _decisive(p): co[k] = 'yes' if p >= 0.5 else 'no'; n += 1
    p = a['invite_confirmed']['noul']
    if _decisive(p) and co.get('invite_confirmed') != 'not_applicable': co['invite_confirmed'] = 'yes' if p >= 0.5 else 'no'
    ob = set(co.get('objections') or [])
    for k, name in (('objection_already_have_vendor', 'already_have_vendor'), ('objection_send_info', 'send_info'),
                    ('objection_not_decision_maker', 'not_decision_maker')):
        p = a[k]['noul']
        if _decisive(p): (ob.add(name) if p >= 0.5 else ob.discard(name)); n += 1
    co['objections'] = sorted(ob)
    h = a['hubspot_status']
    # 'active' needs the prospect's own words: only accept Jev's confident verdict when it is NOT 'active' unless the LLM agrees
    if h.get('confidence', 0) >= 0.8 and h['choice'] in props.ENUMS['hubspot_status']:
        if h['choice'] != 'active' or sig.get('hubspot_status') == 'active':
            sig['hubspot_status'] = h['choice']; n += 1
    m = a['outsources_marketing']
    if m.get('confidence', 0) >= 0.8 and m['choice'] in ('yes', 'no', 'unclear'): sig['outsources_marketing'] = m['choice']
    return n


def _tokens(t): return re.sub(r'[^a-z0-9 ]+', ' ', (t or '').lower()).split()


def quote_supported(quote, transcript, threshold=0.6):
    """True if most 3-word runs of the quote occur in the transcript (tolerates removed filler words)."""
    q = _tokens(quote)
    if len(q) < 4: return True
    T = ' '.join(_tokens(transcript))
    sh = [' '.join(q[i:i + 3]) for i in range(len(q) - 2)]
    return sum(s in T for s in sh) / len(sh) >= threshold


def _sanity(sig, co, transcript):
    """Self-consistency and evidence checks, applied before anything is written."""
    # a definite HubSpot verdict must be backed by a quote that really is in the transcript
    st = sig.get('hubspot_status')
    if st in ('active', 'considering', 'churned', 'never'):
        q = ((sig.get('rationale') or {}).get('hubspot_status') or '').split(' | ')[0].strip().strip('"')
        if not q or not quote_supported(q, transcript): sig['hubspot_status'] = 'unconfirmed'
    ob = [o for o in (co.get('objections') or []) if o != 'none']
    co['objections'] = ob
    if ob and co.get('objection_handling') == 'no_objection': co.pop('objection_handling')
    stage = (co.get('stage_reached') or '')[:3]
    booked = stage in ('s10', 's11', 's12')
    if stage in ('s11', 's12') and co.get('asked_for_meeting') == 'no': co['asked_for_meeting'] = 'yes'
    if co.get('invite_confirmed') == 'yes' and not booked: co['invite_confirmed'] = 'no'
    if sig.get('budget_status') == 'stated' and not sig.get('budget_amount'): sig['budget_status'] = 'discussed_no_figure'


def score_transcript(transcript, call_date):
    """Returns (properties, model_name) or (None, None) on failure."""
    with cf.ThreadPoolExecutor(2) as ex:
        fj = ex.submit(jev, transcript, prompts.JEV_QUESTIONS)
        fg = ex.submit(gemini, prompts.HYBRID_PROMPT % (call_date, transcript[:30000]))
        a = fj.result(); o, model = fg.result()
    if 'error' in o or 'signals' not in o or 'coaching' not in o: return None, None
    sig, co = o['signals'], o['coaching']
    try: _merge_jev(sig, co, a)
    except Exception: pass
    _sanity(sig, co, transcript)
    p = props.signal_props(sig); p.update(props.coach_props(co))
    return p, model


def notes_text(p):
    """Text from HubSpot AI summary / tracked terms / the rep's typed notes (no transcript available)."""
    parts = []
    for k, label in (('hs_call_summary', 'HubSpot call summary'), ('hs_ai_summary', 'AI summary'),
                     ('hs_call_transcript_tracked_terms', 'Tracked terms')):
        if p.get(k): parts.append('%s: %s' % (label, p[k]))
    b = BOILERPLATE.sub('', p.get('hs_call_body') or '').replace('CAS Call Notes:', '').strip()
    b = re.sub(r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M:', '', b).strip()
    if len(b) >= 40: parts.append('Rep notes: ' + b)
    return '\n'.join(parts)


def score_notes(text, call_date):
    """Signals only (no coaching), marked source=call_summary."""
    o, model = gemini(prompts.SUMMARY_PROMPT % (call_date, text[:12000]))
    if 'error' in o: return None, None
    return props.signal_props(o, source='call_summary'), model
