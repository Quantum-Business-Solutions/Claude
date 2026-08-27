#!/usr/bin/env python3
"""
Runnable QA gates for the AI Lead Finder pipeline.

Run the matching gate between every stage. Each returns non-zero on failure so
it can't be skipped by accident. Every check here corresponds to a bug that
shipped wrong data during the UBEO run — see references/failure-modes.md.

  python3 qa_gates.py harvest  --pool pool.json --ledger done.json --terms terms.json
  python3 qa_gates.py extract  --signals signals.json --pool pool.json
  python3 qa_gates.py write    --signals signals.json --obj tasks --prop ai__lease_information
  python3 qa_gates.py rollup   --signals signals.json --assoc assoc.json --companies companies.json

PAT must be in the environment for the `write` gate.
"""
import json, os, sys, re, argparse, urllib.request, time, collections, datetime

FAIL = []
WARN = []

def fail(msg): FAIL.append(msg)
def warn(msg): WARN.append(msg)
def ok(msg):   print("  \033[32m✓\033[0m %s" % msg)

def load(p):
    with open(p) as f: return json.load(f)

def api(obj, body):
    r = urllib.request.Request(
        "https://api.hubapi.com/crm/v3/objects/%s/search" % obj,
        data=json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + os.environ['PAT'],
                 'Content-Type': 'application/json'}, method='POST')
    return json.load(urllib.request.urlopen(r))


# ───────────────────────── GATE 1 — HARVEST ─────────────────────────
def gate_harvest(a):
    pool = load(a.pool)
    print("\nGATE 1 — HARVEST  (pool: %s records)\n" % format(len(pool), ","))

    # 1. every planned term actually ran
    if a.ledger and a.terms:
        done, terms = set(load(a.ledger)), load(a.terms)
        fields = a.fields.split(",") if a.fields else []
        want = {"%s|%s" % (f, t) for f in fields for t in terms} if fields else set()
        missing = want - done
        if missing:
            fail("%d term×field combos never ran — e.g. %s"
                 % (len(missing), sorted(missing)[:3]))
        else:
            ok("all %d term×field combos present in ledger" % len(want))

    # 2. THE BIG ONE — cap truncation
    if a.per_term:
        counts = load(a.per_term)
        capped = {t: n for t, n in counts.items() if 9800 <= n <= 10000}
        if capped:
            fail("SEARCH CAP TRUNCATION on %d term(s): %s — re-run these date-windowed"
                 % (len(capped), list(capped)[:5]))
        else:
            ok("no term sits in the 9,800–10,000 truncation band")

    # 3. pool plausibility
    if len(pool) < 1000:
        warn("pool of %s is very small — check the term set actually applied" % format(len(pool), ","))
    else:
        ok("pool size plausible")

    # 4. records must carry text
    empty = sum(1 for r in pool.values()
                if not any((r.get("properties") or {}).get(k) for k in
                           (r.get("properties") or {}) if k != "hs_timestamp"))
    if empty > 0.5 * len(pool):
        warn("%.0f%% of pooled records have no text in the requested properties — "
             "are you harvesting one field and reading another?" % (100 * empty / len(pool)))
    else:
        ok("pooled records carry text")


# ───────────────────────── GATE 2 — EXTRACT ─────────────────────────
def gate_extract(a):
    rows = load(a.signals)
    print("\nGATE 2 — EXTRACT  (%s signals)\n" % format(len(rows), ","))

    # 1. basis phrase must appear in its own evidence
    orphan = [x for x in rows
              if x.get("basis") and x["basis"].split(" term,")[0].lower()
              not in (x.get("body") or "").lower()]
    if orphan:
        fail("%d signals whose basis phrase is absent from their own body — "
             "evidence excerpt is sliced from the wrong place" % len(orphan))
    else:
        ok("every signal contains its own basis phrase")

    # 2. yield plausibility
    if a.pool:
        pool = load(a.pool)
        y = 100 * len(rows) / max(len(pool), 1)
        if y > 8:
            fail("yield %.1f%% is far above the 1–3%% norm — expect false positives" % y)
        elif y < 0.3:
            warn("yield %.2f%% is below the 1–3%% norm — suspect a field or pattern gap" % y)
        else:
            ok("yield %.1f%% within expected 1–3%% band" % y)

    # 3. projection must not dominate
    src = collections.Counter(x.get("src", "?") for x in rows)
    proj = sum(v for k, v in src.items() if "projected" in k)
    conf = sum(v for k, v in src.items() if k.startswith("stated"))
    if conf and proj > 3 * conf:
        warn("projected (%d) exceeds confirmed (%d) by more than 3:1 — "
             "check the projection cap is one cycle" % (proj, conf))
    else:
        ok("projection/confirmed ratio sane (%d/%d)" % (proj, conf))

    # 4. Jan-1 clustering => year-only pinning not firing
    jan1 = [x for x in rows if str(x.get("end", "")).endswith("-01-01")]
    if len(jan1) > 0.05 * max(len(rows), 1):
        fail("%d signals land on Jan 1 (%.0f%%) — year-only dates are not being "
             "pinned to 10/31" % (len(jan1), 100 * len(jan1) / len(rows)))
    else:
        ok("no Jan-1 cluster; year-only pinning is firing")

    # 5. implausible years
    bad = [x for x in rows if not re.match(r"^20[2-3]\d-", str(x.get("end", "")))]
    if bad:
        warn("%d signals with implausible end years — flag, do not silently delete" % len(bad))
    else:
        ok("all end dates fall in a plausible range")

    # 6. exclusions actually populated
    flags = collections.Counter(f for x in rows for f in x.get("flags", []))
    if not flags:
        fail("no classification flags present at all — the exclusion stage did not run")
    else:
        ok("classification flags present: %s" % dict(flags))

    # 7. MANDATORY HUMAN STEP
    print("\n  \033[33m▲ READ 10–15 OF THESE RECORDS YOURSELF BEFORE PROCEEDING.\033[0m")
    print("    Every precision bug in the first run was caught by reading output,")
    print("    and none by aggregate statistics. Sample across confidence tiers.\n")
    for x in rows[:3]:
        b = re.sub(r"\s+", " ", str(x.get("body", "")))[:120]
        print("      [%s] %s" % (x.get("src", "?"), b))


# ───────────────────────── GATE 3 — WRITE ─────────────────────────
def gate_write(a):
    rows = load(a.signals)
    print("\nGATE 3 — WRITE  (%s expected on %s)\n" % (format(len(rows), ","), a.obj))

    ids = [x["engagement_id"] for x in rows][:5]
    # direct GET — search index lags writes and will under-report
    live = 0
    for i in ids:
        r = urllib.request.Request(
            "https://api.hubapi.com/crm/v3/objects/%s/%s?properties=%s" % (a.obj, i, a.prop),
            headers={'Authorization': 'Bearer ' + os.environ['PAT']})
        v = (json.load(urllib.request.urlopen(r))["properties"] or {}).get(a.prop)
        if v and v.strip(): live += 1
    if live == len(ids):
        ok("direct GET confirms writes landed (%d/%d sampled)" % (live, len(ids)))
    else:
        fail("only %d/%d sampled records carry a value on direct GET" % (live, len(ids)))

    print("  waiting 45s for the search index to settle…")
    time.sleep(45)
    total = api(a.obj, {"limit": 1, "filterGroups": [
        {"filters": [{"propertyName": a.prop, "operator": "HAS_PROPERTY"}]}]}).get("total", 0)
    if total < 0.95 * len(rows):
        warn("search reports %s vs %s expected — re-check; index may still be lagging"
             % (format(total, ","), format(len(rows), ",")))
    else:
        ok("search index agrees: %s populated" % format(total, ","))

    # format compliance
    bad_fmt = [x for x in rows[:200] if not re.match(r"^\d{4}/\d{2} ", str(x.get("value", "YYYY/MM ")))]
    if a.check_format and bad_fmt:
        fail("%d values do not lead with YYYY/MM — text fields sort as strings, "
             "MM/YYYY sorts backwards" % len(bad_fmt))


# ───────────────────────── GATE 4 — ROLLUP ─────────────────────────
def gate_rollup(a):
    sigs = {x["engagement_id"]: x for x in load(a.signals)}
    assoc = load(a.assoc)
    comps = load(a.companies)
    print("\nGATE 4 — ROLLUP\n")

    # 1. stranded signals reported, not hidden
    stranded = [e for e in sigs if e not in assoc]
    if stranded:
        warn("%d signals have no company association — stranded on the engagement "
             "record. Report these; do not drop silently." % len(stranded))
    else:
        ok("every signal resolves to a company")

    # 2. THE BIG ONE — no customer carries a value
    cust = [e for e, c in assoc.items()
            if (comps.get(str(c)) or {}).get("lifecyclestage") == "customer"]
    if cust:
        fail("%d engagement records belong to CUSTOMER companies. Clear the property "
             "on the engagements too — gating only at rollup leaves them visible to "
             "reps browsing activity." % len(cust))
    else:
        ok("no customer-company engagement carries a value")

    # 3. don't-downgrade proof
    if a.kept_existing is not None:
        if a.kept_existing == 0:
            warn("kept-existing count is 0 — on a re-run this should be non-zero; "
                 "the don't-downgrade guard may not be working")
        else:
            ok("don't-downgrade guard active (%s companies kept their value)"
               % format(a.kept_existing, ","))

    # 4. association sanity — cheap, catches misfiled intel
    print("\n  \033[33m▲ SPOT-CHECK ASSOCIATIONS.\033[0m A call about one company associated")
    print("    to another puts lease intel on the wrong account. Seen in production.\n")
    for e, c in list(assoc.items())[:3]:
        nm = (comps.get(str(c)) or {}).get("name", "?")
        b = re.sub(r"\s+", " ", str(sigs.get(e, {}).get("body", "")))[:90]
        print("      %-34s ← %s" % (nm[:34], b))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("gate", choices=["harvest", "extract", "write", "rollup"])
    p.add_argument("--pool"); p.add_argument("--ledger"); p.add_argument("--terms")
    p.add_argument("--fields"); p.add_argument("--per-term")
    p.add_argument("--signals"); p.add_argument("--obj"); p.add_argument("--prop")
    p.add_argument("--assoc"); p.add_argument("--companies")
    p.add_argument("--kept-existing", type=int)
    p.add_argument("--check-format", action="store_true")
    a = p.parse_args()

    {"harvest": gate_harvest, "extract": gate_extract,
     "write": gate_write, "rollup": gate_rollup}[a.gate](a)

    if WARN:
        print("\n\033[33mWARNINGS\033[0m")
        for w in WARN: print("  ▲ %s" % w)
    if FAIL:
        print("\n\033[31mFAILURES — DO NOT PROCEED\033[0m")
        for f in FAIL: print("  ✗ %s" % f)
        sys.exit(1)
    print("\n\033[32mGATE PASSED\033[0m\n")


if __name__ == "__main__":
    main()
