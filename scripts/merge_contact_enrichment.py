#!/usr/bin/env python3
"""Merge ZoomInfo contact enrichment into the acquisition decision-maker list.

Keeps the two files separate so the enrichment (which cost credits) is never
lost by a re-run of the upstream screening step.
"""

import csv
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = os.path.join(REPO, "data", "acquisition_decision_makers.csv")
ENRICH = os.path.join(REPO, "data", "zi_contact_enrichment.csv")

COLUMNS = [
    "first_name", "last_name", "email", "title", "authority", "company",
    "domain", "tier", "direct_phone", "mobile_phone", "direct_phone_dnc",
    "mobile_phone_dnc", "employees", "revenue_usd", "location",
    "zi_accuracy", "zi_last_validated", "zi_person_id",
]


def main() -> None:
    enrich = {
        r["zi_person_id"]: r
        for r in csv.DictReader(open(ENRICH, encoding="utf-8-sig"))
    }
    rows, missing = [], []
    for r in csv.DictReader(open(TARGETS, encoding="utf-8-sig")):
        e = enrich.get(r["zi_person_id"])
        if not e:
            missing.append(f"{r['first_name']} {r['last_name']}")
            continue
        merged = dict(r)
        merged.update({k: v for k, v in e.items() if k != "zi_person_id"})
        rows.append({c: merged.get(c, "") for c in COLUMNS})

    # Owners and founders first - they hold the equity.
    rank = {"Owner": 0, "Founder": 1, "Chairman": 2, "CEO": 3,
            "President": 4, "Equity partner": 5, "Managing Director": 6}
    rows.sort(key=lambda r: (0 if r["tier"] == "Elite" else 1,
                             rank.get(r["authority"], 9), r["company"]))

    with open(TARGETS, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    print(f"merged {len(rows)} decision-makers")
    if missing:
        print(f"  ! no enrichment for: {', '.join(missing)}")
    print(f"  with email        {sum(1 for r in rows if r['email'])}")
    print(f"  with any phone    {sum(1 for r in rows if r['direct_phone'] or r['mobile_phone'])}")
    print(f"  mobile marked DNC {sum(1 for r in rows if r['mobile_phone_dnc'] == 'Y')}")
    print(f"  direct marked DNC {sum(1 for r in rows if r['direct_phone_dnc'] == 'Y')}")
    print(f"  accuracy >= 95    {sum(1 for r in rows if int(r['zi_accuracy'] or 0) >= 95)}")
    stale = [r for r in rows
             if not r["zi_last_validated"] or r["zi_last_validated"][:4] < "2026"]
    print(f"  not validated in 2026: {len(stale)}"
          + (f" ({', '.join(r['last_name'] for r in stale)})" if stale else ""))


if __name__ == "__main__":
    main()
