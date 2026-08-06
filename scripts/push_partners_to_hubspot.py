#!/usr/bin/env python3
"""Push the HubSpot partner directory export into HubSpot company records.

Writes the hubspot_partner_* property set. On existing records it touches ONLY
those properties - never name, domain, website, lifecycle stage or owner, because
directory company names are partner-authored marketing copy and overwriting good
CRM values with them would be destructive. On newly created records it also sets
name/domain/website/country/city, where there is nothing to overwrite.

Matching is by domain against the matcher output. HubSpot batch/upsert cannot key
on domain (it requires a property flagged hasUniqueValue, which domain is not), so
updates and creates are issued as separate explicit batches.


Usage:
    export QBS_HUBSPOT_TOKEN=pat-na1-...
    python3 scripts/push_partners_to_hubspot.py --dry-run
    python3 scripts/push_partners_to_hubspot.py
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.hubapi.com"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTNERS_CSV = os.path.join(REPO_ROOT, "data", "hubspot_partners.csv")
SKIPPED_CSV = os.path.join(REPO_ROOT, "data", "partners_not_pushed.csv")
MATCHED_CSV = os.path.join(REPO_ROOT, "data", "partners_matched_in_hubspot.csv")

BATCH = 100
TIER_LABEL = {
    "elite": "Elite", "diamond": "Diamond",
    "platinum": "Platinum", "gold": "Gold", "": "Untiered",
}
TYPE_LABEL = {
    "partner": "Partner", "provider": "Provider",
    "directory_user": "Directory user",
}
TIER_RANK = {"elite": 0, "diamond": 1, "platinum": 2, "gold": 3, "": 4}


def post(token: str, path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode()
    for attempt in range(6):
        req = urllib.request.Request(
            f"{API}{path}", data=body, method="POST",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()[:600]
            if exc.code == 429 or exc.code >= 500:
                time.sleep(min(2**attempt, 20))
                continue
            raise RuntimeError(f"HTTP {exc.code} on {path}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError):
            time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"gave up on {path}")


def dedupe_by_domain(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """One row per domain. Some companies run two directory profiles.

    Keeps the strongest profile (highest tier, then most reviews) so the surviving
    record reflects the company's best credential rather than whichever row came
    last in the file.
    """
    best: dict[str, dict] = {}
    dropped: list[dict] = []
    for row in rows:
        dom = row["domain"]
        cur = best.get(dom)
        if cur is None:
            best[dom] = row
            continue
        key = lambda r: (TIER_RANK.get(r["tier"], 4), -int(r["review_count"] or 0))
        if key(row) < key(cur):
            best[dom] = row
            dropped.append(cur)
        else:
            dropped.append(row)
    return list(best.values()), dropped


def build_props(row: dict, today: str) -> dict:
    props = {
        "hubspot_partner": "true",
        "hubspot_partner_tier": TIER_LABEL.get(row["tier"], "Untiered"),
        "hubspot_partner_directory_url": row["directory_url"],
        "hubspot_partner_synced_on": today,
    }
    if row["country"]:
        props["hubspot_partner_country"] = row["country"]
    ptype = TYPE_LABEL.get(row["partner_type"])
    if ptype:
        props["hubspot_partner_type"] = ptype
    if row["accreditations"]:
        # HubSpot multi-select checkbox expects semicolon-separated values.
        props["hubspot_partner_accreditations"] = row["accreditations"]
    if row["review_count"]:
        props["hubspot_partner_review_count"] = row["review_count"]
    if row["rating"]:
        props["hubspot_partner_rating"] = row["rating"]
    if row["partner_id"]:
        props["hubspot_partner_id"] = row["partner_id"]
    return props


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("QBS_HUBSPOT_TOKEN", ""))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if not args.token:
        print("set QBS_HUBSPOT_TOKEN", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(open(PARTNERS_CSV, encoding="utf-8-sig")))
    with_domain = [r for r in rows if r["domain"]]
    no_domain = [r for r in rows if not r["domain"]]
    unique, dropped = dedupe_by_domain(with_domain)
    unique.sort(key=lambda r: (TIER_RANK.get(r["tier"], 4),
                               -int(r["review_count"] or 0)))
    if args.limit:
        unique = unique[: args.limit]

    print(f"partners in export        {len(rows)}")
    print(f"  no usable domain       {len(no_domain)}  (cannot upsert - skipped)")
    print(f"  duplicate domain       {len(dropped)}  (weaker profile skipped)")
    print(f"  to upsert              {len(unique)}")

    # Record what we did not push, so the gap is visible rather than silent.
    skipped = ([dict(r, skip_reason="no usable domain") for r in no_domain]
               + [dict(r, skip_reason="duplicate domain, weaker profile")
                  for r in dropped])
    if skipped:
        with open(SKIPPED_CSV, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(skipped[0].keys()))
            w.writeheader()
            w.writerows(skipped)
        print(f"  wrote {SKIPPED_CSV}")

    today = time.strftime("%Y-%m-%d")

    # batch/upsert cannot key on domain: HubSpot requires a *unique* property and
    # companies may legitimately share a domain. So split explicitly - update the
    # records the matcher already resolved to an ID, create the rest.
    matched_by_domain: dict[str, str] = {}
    if os.path.exists(MATCHED_CSV):
        for m in csv.DictReader(open(MATCHED_CSV, encoding="utf-8-sig")):
            matched_by_domain[m["domain"]] = m["hs_company_id"]

    updates, creates = [], []
    for row in unique:
        props = build_props(row, today)
        hs_id = matched_by_domain.get(row["domain"])
        if hs_id:
            updates.append({"id": hs_id, "properties": props})
        else:
            # New record: safe to set core fields, nothing to overwrite. Uses the
            # slug-derived name, never the directory's marketing-copy name.
            create_props = dict(props)
            create_props["name"] = row["company_name"]
            create_props["domain"] = row["domain"]
            if row["website"]:
                create_props["website"] = row["website"]
            if row["country"]:
                create_props["country"] = row["country"]
            if row["city"]:
                create_props["city"] = row["city"]
            creates.append({"properties": create_props})

    print(f"    -> update existing   {len(updates)}")
    print(f"    -> create new        {len(creates)}")

    if args.dry_run:
        print("\n--- dry run ---")
        if updates:
            print("UPDATE sample:", json.dumps(updates[0], indent=1))
        if creates:
            print("CREATE sample:", json.dumps(creates[0], indent=1))
        return 0

    def run(path: str, items: list[dict], label: str) -> tuple[int, int]:
        ok = bad = 0
        for i in range(0, len(items), BATCH):
            chunk = items[i : i + BATCH]
            try:
                post(args.token, path, {"inputs": chunk})
                ok += len(chunk)
            except RuntimeError as exc:
                bad += len(chunk)
                print(f"\n  ! {label} batch at {i}: {exc}", file=sys.stderr)
            print(f"  {label}: {ok + bad}/{len(items)} (ok {ok}, failed {bad})",
                  end="\r", flush=True)
            time.sleep(0.2)
        if items:
            print()
        return ok, bad

    up_ok, up_bad = run("/crm/v3/objects/companies/batch/update", updates, "update")
    cr_ok, cr_bad = run("/crm/v3/objects/companies/batch/create", creates, "create")

    print(f"\nupdated {up_ok} | created {cr_ok} | failed {up_bad + cr_bad}")
    return 0 if not (up_bad + cr_bad) else 1


if __name__ == "__main__":
    sys.exit(main())
