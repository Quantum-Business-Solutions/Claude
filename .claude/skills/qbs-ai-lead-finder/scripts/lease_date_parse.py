"""Parse the leading YYYY/MM off ai__lease_information and turn it into a real
HubSpot date for 'AI - Potential Lease End Date'.

The text field stays exactly as it is - it carries the evidence and the citation.
This adds a sortable, filterable, workflow-usable date beside it.
"""
import re, datetime, calendar

PREFIX = re.compile(r"^\s*(20\d{2})/(0?[1-9]|1[0-2])\b")
TIER    = re.compile(r"^\s*20\d{2}/\d{1,2}\s*\[([^\]]+)\]")
PINNED  = re.compile(r"pinned (?:to )?10/31|year only|start month unknown|month not stated|month never confirmed", re.I)

def parse(val):
    """-> (date, tier, month_is_real) or None."""
    if not val: return None
    m = PREFIX.match(val)
    if not m: return None
    y, mo = int(m.group(1)), int(m.group(2))
    if not (2015 <= y <= 2040): return None
    t = TIER.match(val)
    tier = (t.group(1).strip() if t else "UNSPECIFIED")
    month_real = not bool(PINNED.search(val))
    # HubSpot date properties are midnight UTC. Use the LAST day of the stated
    # month: a lease "ending 2027/03" is not over until March is over, and a
    # first-of-month date makes every list look a month more urgent than it is.
    d = datetime.date(y, mo, calendar.monthrange(y, mo)[1])
    return d, tier, month_real

def to_hubspot(d):
    return str(int(datetime.datetime(d.year, d.month, d.day,
                                     tzinfo=datetime.timezone.utc).timestamp() * 1000))

if __name__ == "__main__":
    import json, glob, collections
    vals = {}
    for fn in glob.glob("*_values.json") + ["v2_company_writes.json"]:
        try: vals.update(json.load(open(fn)))
        except Exception: pass
    ok, fail, tiers, pinned = 0, [], collections.Counter(), 0
    for k, v in vals.items():
        r = parse(v)
        if r is None: fail.append((k, (v or "")[:90])); continue
        ok += 1; tiers[r[1]] += 1
        if not r[2]: pinned += 1
    print("value strings checked : %s" % format(len(vals), ","))
    print("  parsed to a date    : %s" % format(ok, ","))
    print("  no leading YYYY/MM  : %s" % format(len(fail), ","))
    print("  month is a pin, not stated : %s" % format(pinned, ","))
    print("\ntier prefix found in the string:")
    for t, n in tiers.most_common(): print("   %-22s %s" % (t, format(n, ",")))
    if fail:
        print("\nunparseable samples:")
        for k, v in fail[:8]: print("   %s  %r" % (k, v))
