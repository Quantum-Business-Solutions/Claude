#!/usr/bin/env python3
"""Build and maintain the LinkedIn engagement roster.

WHY THIS EXISTS IN THIS SHAPE
-----------------------------
The original watch-sync scraped Sales Navigator through a local browser and
never completed a single run, because Cowork scheduled tasks execute remotely.
The proposed replacement -- feed a Sales Nav list URL to Unipile's
``/linkedin/search`` -- cannot work either: verified 2026-08-29, every Sales
Navigator route returns ``401 errors/invalid_credentials`` on BOTH of Shawn's
accounts while Classic routes return 200. The premium entitlement is present;
the Unipile Sales Nav *session* is not. So the roster comes from HubSpot,
which is reachable, authoritative, and already the system of record.

THE REAL JOB
------------
Resolving provider IDs. ``GET /users/{id}/posts`` REJECTS a vanity slug with
422 -- it requires the LinkedIn member id (ACo...). Only 29 of 153,330
contacts carry one today, so without this step the engagement routine has
almost nobody whose posts it can fetch. Every resolved id is also written to
``hublead_linkedin_member_id``, which is unique and immutable, so a prospect
renaming their vanity URL can never silently drop off the roster again.

THE SPLIT
---------
Unipile sits behind a non-443 port the agent proxy does not carry, so this
script cannot call it. Same contract as contact-verification:

    plan   -- read HubSpot, emit the work queue as JSON   (this script)
    <the routine resolves each profile via the Unipile MCP>
    write  -- take the resolved JSON, write back to HubSpot  (this script)

Deterministic work is code; the calls that need MCP are the routine's.

Usage:
    python3 scripts/watch_sync.py plan  --list-id 5243 [--limit 100] > queue.json
    python3 scripts/watch_sync.py write --input resolved.json [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qbs_linkedin import config as cfg  # noqa: E402
from qbs_linkedin.normalize import (  # noqa: E402
    UrlError,
    canonical_url,
    choose_profile_url,
    extract_slug,
)

API = "https://api.hubapi.com"
EXIT_OK, EXIT_ENV = 0, 2

ROSTER_PROPERTIES = [
    "firstname", "lastname", "company", "jobtitle",
    cfg.UPSERT_KEY_PROPERTY, "hs_linkedin_url",
    cfg.SECONDARY_MATCH_PROPERTY, cfg.AI_STILL_AT_COMPANY,
]


def _token() -> str:
    tok = os.environ.get("QBS_HUBSPOT_TOKEN", "").strip()
    if not tok:
        sys.exit("QBS_HUBSPOT_TOKEN unset")
    return tok


def _request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            # 429 is HubSpot throttling; anything else is a real error.
            if exc.code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("unreachable")


def fetch_roster(token: str, list_id: str, limit: int | None) -> list[dict]:
    """Read list membership, then batch-read the properties we need.

    Membership returns record ids only, so the properties are a second call.
    """
    ids: list[str] = []
    after = None
    while True:
        qs = "?limit=100" + (f"&after={after}" if after else "")
        page = _request("GET", f"/crm/v3/lists/{list_id}/memberships{qs}", token)
        ids += [str(r["recordId"]) for r in page.get("results", [])]
        after = (page.get("paging") or {}).get("next", {}).get("after")
        if not after or (limit and len(ids) >= limit):
            break
    if limit:
        ids = ids[:limit]

    rows: list[dict] = []
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        got = _request("POST", "/crm/v3/objects/contacts/batch/read", token, {
            "properties": ROSTER_PROPERTIES,
            "inputs": [{"id": cid} for cid in chunk],
        })
        rows += got.get("results", [])
    return rows


def build_queue(rows: list[dict]) -> dict:
    """Classify every roster member. Nothing ambiguous is passed through."""
    ready, needs_resolution, skipped = [], [], []

    for row in rows:
        props = row.get("properties", {})
        first = props.get("firstname")
        last = props.get("lastname")
        name = " ".join(x for x in (first, last) if x) or "(no name)"

        if props.get(cfg.AI_STILL_AT_COMPANY) == cfg.VERDICT_NO:
            skipped.append({"contact_id": row["id"], "name": name,
                            "reason": "verified as no longer at this company"})
            continue

        url, problem = choose_profile_url(
            props.get(cfg.UPSERT_KEY_PROPERTY),
            props.get("hs_linkedin_url"),
            first, last,
        )
        if problem:
            # Conflicting or unusable URLs go to review, never to a guess:
            # 1.3% of contacts carry two URLs pointing at different people.
            skipped.append({"contact_id": row["id"], "name": name,
                            "reason": problem})
            continue

        entry = {
            "contact_id": row["id"],
            "name": name,
            "company": props.get("company"),
            "profile_url": url,
            "public_identifier": extract_slug(url),
        }
        provider_id = props.get(cfg.SECONDARY_MATCH_PROPERTY)
        if provider_id:
            entry["provider_id"] = provider_id
            ready.append(entry)
        else:
            needs_resolution.append(entry)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ready": ready,
        "needs_resolution": needs_resolution,
        "skipped": skipped,
        "counts": {
            "ready": len(ready),
            "needs_resolution": len(needs_resolution),
            "skipped": len(skipped),
            "total": len(rows),
        },
    }


def write_back(token: str, resolved: list[dict], dry_run: bool) -> dict:
    """Persist resolved provider IDs and canonical URLs.

    Batched by contact id -- NOT upserted by the unique URL. An upsert here
    would create a contact on any key miss, and the whole point of this step
    is that we already know the record id.
    """
    updates, rejected = [], []
    for item in resolved:
        cid, pid = item.get("contact_id"), item.get("provider_id")
        if not cid or not pid:
            rejected.append({**item, "reason": "missing contact_id or provider_id"})
            continue
        if not pid.startswith(("ACo", "ADo")):
            rejected.append({**item, "reason": f"{pid!r} is not a LinkedIn member id"})
            continue
        props = {cfg.SECONDARY_MATCH_PROPERTY: pid}
        if item.get("profile_url"):
            try:
                props[cfg.UPSERT_KEY_PROPERTY] = canonical_url(item["profile_url"])
            except UrlError as exc:
                rejected.append({**item, "reason": str(exc)})
                continue
        updates.append({"id": str(cid), "properties": props})

    written = 0
    if updates and not dry_run:
        for i in range(0, len(updates), 100):
            _request("POST", "/crm/v3/objects/contacts/batch/update", token,
                     {"inputs": updates[i:i + 100]})
            written += len(updates[i:i + 100])

    return {
        "written": written,
        "would_write": len(updates) if dry_run else 0,
        "rejected": rejected,
        "dry_run": dry_run,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="read HubSpot, emit the work queue")
    p.add_argument("--list-id", required=True)
    p.add_argument("--limit", type=int)

    w = sub.add_parser("write", help="write resolved provider IDs back")
    w.add_argument("--input", required=True, help="JSON file, or - for stdin")
    w.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    token = _token()

    if args.command == "plan":
        rows = fetch_roster(token, args.list_id, args.limit)
        queue = build_queue(rows)
        print(json.dumps(queue, indent=2))
        # A roster that resolves nobody is a failure, not a quiet success.
        # watch-sync reported lastRunAt normally for months while producing
        # nothing; a zero result must be loud.
        if queue["counts"]["ready"] == 0 and queue["counts"]["needs_resolution"] == 0:
            print("ROSTER EMPTY - nothing engageable in this list",
                  file=sys.stderr)
            return EXIT_ENV
        return EXIT_OK

    payload = (json.load(sys.stdin) if args.input == "-"
               else json.load(open(args.input)))
    resolved = payload if isinstance(payload, list) else payload.get("resolved", [])
    print(json.dumps(write_back(token, resolved, args.dry_run), indent=2))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
