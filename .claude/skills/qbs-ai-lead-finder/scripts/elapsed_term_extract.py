"""ELAPSED-term derivation.

The main extractor reads REMAINING term ("3 yrs left"). A second, equally datable
class states ELAPSED term ("a year and a half into their contract"). Read naively
these invert: 1.5 years INTO a lease is 3.5 years LEFT, not 1.5.

  stated total term   -> CALCULATED  (5-yr term, 2 yrs in  -> 3 yrs out)
  no total stated     -> PROJECTED   (assumes the 60-month copier convention)

Never downgrades: any engagement already carrying a signal is skipped.
"""
import json, re, sys, datetime, collections

TODAY = datetime.date(2026, 8, 29)
DEFAULT_TERM_MO = 60          # the copier industry convention; always disclosed in the evidence

def clean(t):
    return re.sub(r'\s+',' ', re.sub('<[^>]+>',' ', t or '')
                  .replace('&nbsp;',' ').replace('&amp;','&').replace('&#x27;',"'")).strip()
QUOTED  = re.compile(r'(?is)(?:^|\n)\s*(?:On .{0,80}?wrote:|-{2,}\s*Original Message|From:\s.{0,60}?Sent:|_{5,}|>{1,}\s).*$')
SIGBLOCK= re.compile(r'(?is)(?:\n|^)\s*(?:Sincerely|Regards|Best regards|Thanks?,|Thank you,)[\s,]*\n.*$')
def strip_thread(t): return SIGBLOCK.sub(' ', QUOTED.sub(' ', t or ''))
def sentences(t): return re.split(r'(?<=[.!?])\s+|\n{2,}|\|\|', t or '')

W = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'a':1,'an':1,'couple':2,'few':3}
ORD = {'first':1,'1st':1,'second':2,'2nd':2,'third':3,'3rd':3,'fourth':4,'4th':4,'fifth':5,'5th':5}
def num(s):
    if s is None: return None
    s = str(s).lower().strip()
    if s in W: return float(W[s])
    return float(s) if re.match(r'^\d+(\.\d+)?$', s) else None

def add_months(base, mo):
    mo = int(round(mo)); y = base.year + (base.month - 1 + mo)//12; m = (base.month - 1 + mo)%12 + 1
    return datetime.date(y, m, min(base.day, 28))

OEM = re.compile(r'\b(Ricoh|Xerox|Canon|Konica(?:\s+Minolta)?|Minolta|Sharp|Toshiba|Kyocera|Lanier|Savin|Muratec|Lexmark|Brother|Epson|Pitney|Stratix|Marco|Impact|Datamax)\b', re.I)

HALF = r'(?:(?:and|&)\s+(?:a\s+)?half\s*)?'
DUR  = r'(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|a|an|couple|few)'
UNIT = r'(yrs?|years?|months?|mos?)'
# "2 years into a 5 year lease"  -> both numbers known
E_TOTAL = re.compile(DUR+r'\s*'+HALF+r'\s*'+UNIT+r'?\s+into\s+(?:a|an|their|the|our)?\s*(?:new\s+)?(\d+)\s*[- ]?(yrs?|years?|months?|mos?)\b', re.I)
# "a year and a half into their contract" -> elapsed only
E_ONLY  = re.compile(r'(?:'+DUR+r'\s*'+HALF+r'\s*'+UNIT+r'|(?:a\s+)?year\s+(?:and|&)\s+(?:a\s+)?half)\s+into\s+(?:a|an|their|the|our)?\s*(?:new\s+|current\s+)?(?:lease|contract|agreement|term|deal)\b', re.I)
# "in the second year of a 5 year lease"
E_ORD   = re.compile(r'\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s+year\s+of\s+(?:a|an|their|the|our)?\s*(?:(\d+)\s*[- ]?(?:yrs?|years?)\s*)?(?:lease|contract|agreement|term|deal)', re.I)
# "just renewed for 5 years" / "recently renewed"
R_TERM  = re.compile(r'\b(?:just|recently|newly|only\s+just)\s+(?:renewed|re-?signed|signed)\b[^.]{0,50}?\bfor\s+(?:another\s+)?'+DUR+r'\s*'+UNIT, re.I)
R_BARE  = re.compile(r'\b(?:just|recently|newly)\s+(?:renewed|re-?signed|signed)\b(?![^.]{0,30}\bnot\b)', re.I)
R_YEAR  = re.compile(r'\b(?:renewed|re-?signed|signed|started)\b(?:\s+(?:a|an|the|their|our|new)){0,3}\s*(?:(\d+)\s*[- ]?(?:yr|yrs|year|years)\s*)?(?:lease|contract|agreement|deal|term)?\s*\b(?:in|back in)\s+(20\d{2})\b(?:[^.]{0,25}?\bfor\s+'+DUR+r'\s*'+UNIT+r')?', re.I)
CALLBACK = re.compile(r"\b(?:call|try|follow(?:ing)?[- ]?up|reach out|check|touch base|contact)\s+(?:me\s+|them\s+|him\s+|her\s+)?(?:back\s+)?(?:again\s+)?(?:in|around|early|late|by)\b", re.I)
NEG     = re.compile(r"\b(?:not|isn'?t|aren'?t|won'?t|didn'?t|never|no longer|hasn'?t)\b", re.I)

def months(v, unit):
    if v is None: return None
    u = (unit or 'year').lower()
    return v * (1 if u.startswith('m') else 12)

def derive(sent, ts):
    """-> (end, src, basis, tier, term_months, year_only) or None. sent is ONE sentence."""
    s = sent.strip()
    if len(s) < 12: return None
    m = E_TOTAL.search(s)
    if m:
        el = num(m.group(1))
        if el is None: return None
        if re.search(r'(?:and|&)\s+(?:a\s+)?half', m.group(0), re.I): el += 0.5
        el_mo = months(el, m.group(2) or 'year')
        tot_mo = months(float(m.group(3)), m.group(4))
        if tot_mo and el_mo is not None and 0 <= el_mo < tot_mo and tot_mo <= 120:
            return add_months(ts, tot_mo - el_mo), "computed from elapsed term against a stated total", m.group(0).strip(), "CALCULATED", tot_mo, False
    m = E_ORD.search(s)
    if m:
        el = ORD[m.group(1).lower()] - 0.5
        tot_mo = months(float(m.group(2)), 'year') if m.group(2) else DEFAULT_TERM_MO
        if 0 <= el*12 < tot_mo:
            tier = "CALCULATED" if m.group(2) else "PROJECTED"
            extra = "" if m.group(2) else " (assumes the 60-month copier term)"
            return add_months(ts, tot_mo - el*12), "computed from elapsed term"+extra, m.group(0).strip(), tier, tot_mo, False
    m = E_ONLY.search(s)
    if m:
        if re.search(r'year\s+(?:and|&)\s+(?:a\s+)?half', m.group(0), re.I): el_mo = 18.0
        else:
            el = num(m.group(1))
            if el is None: return None
            if re.search(r'(?:and|&)\s+(?:a\s+)?half', m.group(0), re.I): el += 0.5
            el_mo = months(el, m.group(2) or 'year')
        if el_mo is None or not (0 <= el_mo < DEFAULT_TERM_MO): return None
        return add_months(ts, DEFAULT_TERM_MO - el_mo), "computed from elapsed term (assumes the 60-month copier term)", m.group(0).strip(), "PROJECTED", DEFAULT_TERM_MO, False
    m = R_YEAR.search(s)
    if m:
        # "renewed for 5 years, call back in 2026" - 2026 is a callback, not a start
        window = s[max(0, m.start()-45):m.start(2) if m.lastindex and m.start(2) > 0 else m.start()]
        if CALLBACK.search(window): m = None
    if m:
        yr = int(m.group(2)); start = datetime.date(yr, 7, 1)
        stated = m.group(1) or m.group(3)
        unit = 'year' if m.group(1) else m.group(4)
        tot_mo = months(num(stated), unit) if stated else DEFAULT_TERM_MO
        if tot_mo and 12 <= tot_mo <= 120 and 2005 <= yr <= TODAY.year:
            tier = "CALCULATED" if stated else "PROJECTED"
            extra = "" if stated else " (assumes the 60-month copier term)"
            return add_months(start, tot_mo), "computed from a stated start year"+extra, m.group(0).strip(), tier, tot_mo, True
    m = R_TERM.search(s)
    if m:
        tot_mo = months(num(m.group(1)), m.group(2))
        if tot_mo and 12 <= tot_mo <= 120:
            return add_months(ts, tot_mo), "computed from a stated renewal term", m.group(0).strip(), "CALCULATED", tot_mo, False
    m = R_BARE.search(s)
    if m and not NEG.search(s[:m.start()]):
        return add_months(ts, DEFAULT_TERM_MO), "computed from a recent renewal (assumes the 60-month copier term)", m.group(0).strip(), "PROJECTED", DEFAULT_TERM_MO, False
    return None

def run(pool_file, typ, body_props, already):
    pool = json.load(open(pool_file))
    out, skipped_existing, rolled = [], 0, 0
    for eid, r in pool.items():
        if eid in already: skipped_existing += 1; continue
        p = r["properties"]
        ts_raw = (p.get("hs_timestamp") or "")[:10]
        if not ts_raw: continue
        try: ts = datetime.date(*map(int, ts_raw.split("-")))
        except Exception: continue
        raw = " || ".join(clean(strip_thread(p.get(k))) for k in body_props if p.get(k))
        if not raw: continue
        best = None
        for sent in sentences(raw):
            d = derive(sent, ts)
            if not d: continue
            rank = {"CALCULATED":2, "PROJECTED":1}[d[3]]
            if not best or rank > best[0]: best = (rank, d)
        if not best: continue
        end, src, basis, tier, term_mo, year_only = best[1]
        flags = []
        if year_only:
            # only the YEAR was stated; July 1 is the midpoint, not a real date
            flags.append("start month unknown - year midpoint used, +/- 6 months")
        if end < TODAY:
            # roll forward by THIS lease's own term, not a flat 60 months
            end = add_months(end, term_mo or DEFAULT_TERM_MO); rolled += 1
            tier = "PROJECTED"
            flags.append("lapsed - rolled forward one cycle")
            if end < TODAY: continue          # still lapsed after one cycle - the cap holds
        if not (TODAY - datetime.timedelta(days=400) <= end <= datetime.date(2034,12,31)): continue
        out.append({"engagement_id":eid, "engagement_type":typ, "ts":ts_raw,
                    "end":end.isoformat(), "basis":basis, "src":src, "tier":tier,
                    "flags":flags, "oem":sorted({m.title() for m in OEM.findall(raw)}),
                    "body":raw[:1200]})
    print("  %-9s pool %-7s already had a signal %-6s NEW %-6s (rolled fwd %d)"
          % (typ, format(len(pool),","), format(skipped_existing,","), format(len(out),","), rolled))
    return out

if __name__ == "__main__":
    already = set()
    for fn in ["call_clean_v10.json","task_clean_v10.json","email_clean_v10.json",
               "meeting_clean_v10.json","note_clean_v10.json"]:
        try:
            for x in json.load(open(fn)): already.add(x["engagement_id"])
        except Exception: pass
    print("existing signals to protect: %s\n" % format(len(already), ","))
    SPEC = [("el_calls_pool.json","call",["hs_call_body","hs_call_summary","hs_call_title"]),
            ("el_tasks_pool.json","task",["hs_task_body","hs_task_subject"]),
            ("el_notes_pool.json","note",["hs_note_body"]),
            ("el_meetings_pool.json","meeting",["hs_meeting_body","hs_meeting_title","hs_internal_meeting_notes"]),
            ("el_emails_pool.json","email",["hs_email_text","hs_email_subject"])]
    allrows = []
    import os
    for fn, typ, props in SPEC:
        if not os.path.exists(fn): print("  %-9s (not harvested yet)" % typ); continue
        allrows += run(fn, typ, props, already)
    json.dump(allrows, open("elapsed_rows.json","w"))
    print("\nNEW ELAPSED-TERM SIGNALS: %s" % format(len(allrows), ","))
    for k, v in collections.Counter(x["tier"] for x in allrows).most_common():
        print("   %-12s %s" % (k, format(v, ",")))
