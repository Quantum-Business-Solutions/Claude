#!/usr/bin/env python3
"""The engagement loop: find posts worth commenting on, then post approved ones.

SPLIT INTO `plan` AND `post`, ON PURPose
----------------------------------------
`plan` reads LinkedIn and HubSpot and emits eligible posts with every guard
already applied. It writes nothing anywhere. `post` takes drafted comments
back and publishes them, re-checking the guards at the moment of the write.

The drafting happens BETWEEN the two, by the agent, and that is deliberate: a
comment published under Shawn's name on a prospect's post is the least
reversible thing this program does, and a template would read as a bot on
exactly the audience it is meant to warm. The script's job is to make sure
nothing unsafe can be published; the judgement about what to say is not the
script's to make.

WHY `post` RE-CHECKS EVERYTHING
------------------------------
Time passes between `plan` and `post` — a human reads the drafts, maybe hours
later. In that window the cap can be consumed by another run, the day can end,
Shawn can comment manually, or the post can have comments turned off. So the
cap, the active-hours window and the dedupe set are all recomputed at write
time. A guard checked only in `plan` is a guard that was true once.

WHAT THIS WILL NOT DO
--------------------
* post as anyone but Shawn (`assert_send_account`, an allowlist)
* post without a live independent count agreeing with the ledger
* post twice on one post (dedupe on EVERY urn a post carries)
* post outside the local active-hours window
* report a send it did not verify as `CommentSent`
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qbs_linkedin import config as cfg
from qbs_linkedin.errors import Action, classify, should_abort_run
from qbs_linkedin.ledger import (
    chicago_day_bounds,
    decide_allowance,
    within_active_hours,
)
from qbs_linkedin.posts import (
    commented_post_ids,
    evaluate_post,
    parse_post_time,
)
from qbs_linkedin.transport import UnipileClient
from qbs_linkedin.unipile import COMMENT_MAX_CHARS, UnipileError

API = "https://api.hubapi.com"
EXIT_OK, EXIT_ENV, EXIT_HALT = 0, 2, 4

#: Posts newer than this are worth commenting on. Set from MEASUREMENT, not
#: taste — `engage.py scan` over the whole 57-person roster on 2026-08-31:
#:
#:     within  2d :  5 of 57        within 30d : 19
#:     within  7d :  7             within 60d : 27
#:     within 14d : 14             within 90d : 29
#:
#: At 48h the roster yields ~5 eligible people at any moment and roughly one
#: NEW post a day across all 57 — which is why the first live run found zero.
#: A week is the honest window: still recent enough that a comment reads as
#: engagement rather than archaeology, and it roughly doubles the pool.
#: Widening further is not the fix for volume — a bigger roster is.
FRESHNESS_HOURS = 24 * 7

#: Pause between LinkedIn reads. v2 returns 429 after roughly four rapid
#: profile reads, so this is not politeness — it is the difference between a
#: run finishing and a run being throttled mid-way.
READ_PAUSE_SECONDS = (4, 9)


def _note(msg: str) -> None:
    """Progress to stderr, so a run that dies still shows how far it got.

    The report is a single JSON document on stdout, which means a crash or an
    external kill loses all of it — which is exactly what happened on the
    first live run of this script. These lines are the difference between
    "stopped at contact 9 of 12" and no information whatsoever.
    """
    print(msg, file=sys.stderr, flush=True)


def _token() -> str:
    tok = os.environ.get("QBS_HUBSPOT_TOKEN", "").strip()
    if not tok:
        sys.exit("QBS_HUBSPOT_TOKEN unset")
    return tok


def _hs(method: str, path: str, token: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        API + path, data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("unreachable")


# --- the ledger, read and written -----------------------------------------

def ledger_counts(token: str) -> tuple[int, int, int]:
    """(posted_today, writes_in_3d, writes_since_epoch) for engagement.

    Counted on the structural marker in the task body, never on the subject:
    HubSpot's CONTAINS_TOKEN is an unanchored AND-of-tokens, so a subject rule
    also matches hand-typed tasks like "Call re: marketing engagement".
    """
    from qbs_linkedin.ledger import LEDGER_EPOCH, LEDGER_STALE_DAYS, date_to_hubspot_date
    from datetime import timedelta

    base = [
        {"propertyName": "hs_task_body", "operator": "CONTAINS_TOKEN",
         "value": cfg.TASK_LEDGER_MARKER},
        {"propertyName": "hubspot_owner_id", "operator": "EQ",
         "value": cfg.SHAWN_OWNER_ID},
    ]

    def count(extra):
        return _hs("POST", "/crm/v3/objects/tasks/search", token,
                   {"filterGroups": [{"filters": base + extra}], "limit": 1}).get("total", 0)

    day_start, day_end = chicago_day_bounds()
    today = count([{"propertyName": cfg.CAP_DATE_PROPERTY, "operator": "BETWEEN",
                    "value": day_start, "highValue": day_end}])
    cutoff = int((datetime.now(timezone.utc) - timedelta(days=LEDGER_STALE_DAYS)).timestamp() * 1000)
    recent = count([{"propertyName": cfg.CAP_DATE_PROPERTY, "operator": "GTE", "value": cutoff}])
    ever = count([{"propertyName": cfg.CAP_DATE_PROPERTY, "operator": "GTE",
                   "value": date_to_hubspot_date(LEDGER_EPOCH)}])
    return today, recent, ever


def log_comment(token: str, contact_id: str, post_url: str, text: str,
                comment_id: str | None) -> str:
    """Write the ledger entry for one posted comment, and associate it.

    The marker in the body is what every count keys on. Without it the entry
    exists but is invisible to the cap, which is how the cap read zero for
    twelve weeks while sends continued.
    """
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    body = (
        f"{cfg.TASK_LEDGER_MARKER}\n"
        f"post: {post_url}\n"
        f"comment_id: {comment_id or '(none returned)'}\n"
        f"account: {cfg.SHAWN_ACCOUNT_ID}\n\n"
        f"{text}"
    )
    task = _hs("POST", "/crm/v3/objects/tasks", token, {
        "properties": {
            "hs_task_subject": f"{cfg.TASK_SUBJECT_PREFIX} comment posted",
            "hs_task_body": body,
            "hs_task_status": "COMPLETED",
            "hs_task_type": cfg.TASK_TYPE_DM,
            "hs_timestamp": now_ms,
            "hubspot_owner_id": cfg.SHAWN_OWNER_ID,
        },
        "associations": [{
            "to": {"id": str(contact_id)},
            "types": [{"associationCategory": "HUBSPOT_DEFINED",
                       "associationTypeId": 204}],
        }],
    })
    return task["id"]


# --- plan -----------------------------------------------------------------

def load_roster(token: str, list_id: str, limit: int | None) -> list[dict]:
    ids, after = [], None
    while True:
        qs = "?limit=100" + (f"&after={after}" if after else "")
        page = _hs("GET", f"/crm/v3/lists/{list_id}/memberships{qs}", token)
        ids += [str(r["recordId"]) for r in page.get("results", [])]
        after = (page.get("paging") or {}).get("next", {}).get("after")
        if not after or (limit and len(ids) >= limit):
            break
    if limit:
        ids = ids[:limit]

    rows = []
    for i in range(0, len(ids), 100):
        got = _hs("POST", "/crm/v3/objects/contacts/batch/read", token, {
            "properties": ["firstname", "lastname", "company", "jobtitle",
                           cfg.SECONDARY_MATCH_PROPERTY, cfg.UPSERT_KEY_PROPERTY],
            "inputs": [{"id": c} for c in ids[i:i + 100]],
        })
        rows += got.get("results", [])
    return rows


def plan(args) -> int:
    token = _token()
    client = UnipileClient()
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "candidates": [], "flagged": [], "skipped": [], "halted": None}

    # 1. The cap, before any per-contact read. No point reading if we cannot post.
    today, recent, ever = ledger_counts(token)
    day_start, day_end = chicago_day_bounds()
    _note(f"ledger: {today} today / {recent} in 3d / {ever} since epoch")

    # ONE fetch of Shawn's comment feed, used for BOTH the independent count
    # and the dedupe set. It is ~2,775 comments over ~28 pages, and fetching
    # it twice was enough on its own to push a run past its time budget.
    try:
        _note("paging Shawn's comment feed (the slow step)...")
        feed = client.self_comments(cfg.SHAWN_PROVIDER_ID)
        # Record it here: client.route holds only the MOST RECENT call, so a
        # single `route` field at the end of the report describes whichever
        # call happened last and quietly misdescribes every other one.
        report["route_self_comments"] = (
            client.route.version if client.route else None)
        _note(f"  feed: {len(feed)} comments via "
              f"{report['route_self_comments']}")
        independent = client.comments_today(cfg.SHAWN_PROVIDER_ID, day_start,
                                           day_end, feed=feed)
        _note(f"  independent count today: {independent}")
    except Exception as exc:
        _note(f"HALT: could not obtain an independent comment count: {exc}")
        report["halted"] = f"independent count unavailable: {exc}"
        print(json.dumps(report, indent=2))
        return EXIT_HALT

    caps = cfg.OutreachCaps()
    decision = decide_allowance(
        posted_today=today, per_day=cfg.COMMENTS_PER_DAY,
        per_run=cfg.COMMENTS_PER_RUN,
        ledger_writes_in_window=recent, ledger_writes_ever=ever,
        independent_count=independent,
    )
    report["cap"] = {"posted_today": today, "ledger_3d": recent,
                     "ledger_since_epoch": ever, "independent_count": independent,
                     "allowance": decision.allowance, "halted": decision.halted,
                     "reason": decision.reason}
    if decision.halted or decision.allowance == 0:
        report["halted"] = decision.reason
        print(json.dumps(report, indent=2))
        return EXIT_HALT if decision.halted else EXIT_OK

    # 2. The dedupe set, from the feed already in hand.
    already = commented_post_ids(feed)
    report["dedupe_set_size"] = len(already)
    _note(f"dedupe set: {len(already)} posts already commented on")

    # 3. Walk the roster until the allowance is filled.
    roster = load_roster(token, args.list_id, args.limit)
    report["roster_size"] = len(roster)
    _note(f"roster: {len(roster)} contacts, allowance {decision.allowance}")
    errors = 0
    deadline = time.monotonic() + args.max_seconds

    for n, row in enumerate(roster, 1):
        if len(report["candidates"]) >= decision.allowance:
            break
        if time.monotonic() > deadline:
            # Stop on our own terms and still print the report. A run killed
            # by an external timeout loses every line of it, which is the
            # silent failure this whole program exists to prevent.
            report["halted"] = (
                f"time budget of {args.max_seconds}s reached after "
                f"{n - 1} contacts — a partial result, not a failure"
            )
            _note(report["halted"])
            break
        props = row.get("properties", {})
        pid = props.get(cfg.SECONDARY_MATCH_PROPERTY)
        name = " ".join(x for x in (props.get("firstname"), props.get("lastname")) if x)
        if not pid or not pid.startswith(("ACo", "ADo")):
            report["skipped"].append({"contact_id": row["id"], "name": name,
                                      "reason": "no valid LinkedIn member id"})
            continue
        try:
            posts = client.posts(pid, limit=10)
        except UnipileError as exc:
            verdict = exc.verdict or classify(None)
            if verdict.action in (Action.HALT, Action.STOP_FOR_DAY):
                report["halted"] = f"{name}: {exc}"
                break
            errors += 1
            report["skipped"].append({"contact_id": row["id"], "name": name,
                                      "reason": f"read failed: {exc}"})
            if should_abort_run(errors, cfg.OutreachThresholds().max_unipile_errors):
                report["halted"] = f"{errors} read errors — something systemic"
                break
            continue

        for post in posts:
            d = evaluate_post(post, already, FRESHNESS_HOURS)
            if d.sensitive:
                # Never comment — but a departure or job change is the
                # earliest mover signal LinkedIn gives us, ahead of any CRM.
                # Dropping it silently throws away the most valuable thing
                # this read found.
                report["flagged"].append({
                    "contact_id": row["id"], "name": name,
                    "company": props.get("company"),
                    "signal": d.sensitive,
                    "post_url": f"https://www.linkedin.com/feed/update/{post.get('social_id')}/",
                    "posted_at": post.get("parsed_datetime"),
                    "excerpt": (post.get("text") or "")[:300],
                    "suggested_action": (
                        "re-verify employment via the Reading Rule and, if it "
                        "confirms, write ai__verification_issue rather than "
                        "engaging"
                        if d.sensitive in ("departure", "job change", "layoff")
                        else "no outreach; human review"
                    ),
                })
                continue
            if not d.eligible:
                report["skipped"].append({"contact_id": row["id"], "name": name,
                                          "post": post.get("social_id"),
                                          "reason": d.reason})
                continue
            report["candidates"].append({
                "contact_id": row["id"], "name": name,
                "company": props.get("company"), "title": props.get("jobtitle"),
                "provider_id": pid,
                "post_social_id": post.get("social_id"),
                "post_url": f"https://www.linkedin.com/feed/update/{post.get('social_id')}/",
                "posted_at": post.get("parsed_datetime"),
                "post_text": (post.get("text") or "")[:1200],
                "reason": d.reason,
                "comment": None,   # <- the agent fills this in
            })
            break   # at most one post per person per run

        _note(f"  [{n}/{len(roster)}] {name}: "
              f"{len(report['candidates'])} candidate(s) so far")
        time.sleep(random.uniform(*READ_PAUSE_SECONDS))

    report["route_posts"] = client.route.version if client.route else None
    print(json.dumps(report, indent=2))
    return EXIT_HALT if report["halted"] else EXIT_OK


# --- scan -----------------------------------------------------------------

def prune_from(args) -> int:
    """Prune the roster using a scan report already on disk.

    Separate from `scan --prune` so the measurement and the list edit are
    independently reviewable: a scan takes minutes of paced LinkedIn reads,
    and re-running it just to apply a decision already made wastes the read
    budget it exists to protect.
    """
    token = _token()
    report = json.load(open(args.input))
    dead = [str(r["contact_id"]) for r in report.get("rows", [])
            if r.get("contact_id") and
            (r.get("newest_original_days") is None or
             r["newest_original_days"] > args.keep_days)]
    if not dead:
        print(json.dumps({"pruned": 0, "reason": "nothing older than "
                          f"{args.keep_days}d"}, indent=2))
        return EXIT_OK
    if args.dry_run:
        print(json.dumps({"would_prune": len(dead), "contact_ids": dead,
                          "dry_run": True}, indent=2))
        return EXIT_OK
    out = _hs("PUT", f"/crm/v3/lists/{args.list_id}/memberships/remove",
              token, [int(c) for c in dead])
    removed = out.get("recordIdsRemoved", [])
    print(json.dumps({"submitted": len(dead), "removed": len(removed),
                      "complete": len(removed) == len(dead)}, indent=2))
    return EXIT_OK


def scan(args) -> int:
    """Measure how recently each roster member actually posts.

    THE PROBLEM THIS SOLVES. The roster was seeded from the verified-callable
    list, which is a CALLING list: it selects for "this person still works
    there and a rep can dial them", not for "this person posts on LinkedIn".
    The first live plan examined 81 posts across 10 of them and found nothing
    eligible — 21 reshares and the rest months old. A daily engagement routine
    against that roster runs forever and finds nothing, which looks exactly
    like the silent failure this program was built to end.

    So the freshness window and the roster are set from measurement, not from
    a guess. This reports, per contact, the age of their newest ORIGINAL post
    (reshares excluded, since we skip those anyway) so the cut can be made on
    evidence.
    """
    token = _token()
    client = UnipileClient()
    roster = load_roster(token, args.list_id, args.limit)
    _note(f"scanning {len(roster)} contacts for real posting activity")

    rows, errors = [], 0
    now = datetime.now(timezone.utc)
    for n, row in enumerate(roster, 1):
        props = row.get("properties", {})
        pid = props.get(cfg.SECONDARY_MATCH_PROPERTY)
        name = " ".join(x for x in (props.get("firstname"), props.get("lastname")) if x)
        if not pid or not pid.startswith(("ACo", "ADo")):
            rows.append({"contact_id": row["id"], "name": name,
                         "error": "no valid member id"})
            continue
        try:
            posts = client.posts(pid, limit=20)
        except UnipileError as exc:
            errors += 1
            rows.append({"contact_id": row["id"], "name": name, "error": str(exc)[:90]})
            verdict = exc.verdict
            if verdict and verdict.action in (Action.HALT, Action.STOP_FOR_DAY):
                _note(f"HALT at {name}: {exc}")
                break
            if should_abort_run(errors, 5):
                _note(f"{errors} read errors — stopping the scan")
                break
            time.sleep(random.uniform(*READ_PAUSE_SECONDS))
            continue

        ages, originals = [], 0
        for post in posts:
            if post.get("is_repost"):
                continue
            when = parse_post_time(post.get(cfg.POST_TIMESTAMP_FIELD))
            if when:
                originals += 1
                ages.append((now - when).days)
        rows.append({
            "contact_id": row["id"], "name": name,
            "company": props.get("company"),
            "provider_id": pid,
            "posts_returned": len(posts),
            "originals": originals,
            "reposts": len(posts) - originals,
            "newest_original_days": min(ages) if ages else None,
        })
        _note(f"  [{n}/{len(roster)}] {name}: newest original "
              f"{rows[-1]['newest_original_days']}d, {originals} originals")
        time.sleep(random.uniform(*READ_PAUSE_SECONDS))

    usable = [r for r in rows if r.get("newest_original_days") is not None]
    dead = [r for r in rows
            if r.get("newest_original_days") is None or
            r["newest_original_days"] > args.keep_days]
    report = {
        "scanned": len(rows),
        "with_original_posts": len(usable),
        "keep_days": args.keep_days,
        "would_prune": [{"contact_id": r["contact_id"], "name": r["name"],
                         "newest_original_days": r.get("newest_original_days")}
                        for r in dead],
        "distribution_days": sorted(r["newest_original_days"] for r in usable),
        "rows": rows,
    }

    if args.prune and dead:
        # Every dead entry costs a Unipile read on every future run, for
        # someone who does not post. Removing them is what keeps a daily run
        # inside its rate budget as the roster grows.
        ids = [int(r["contact_id"]) for r in dead if r.get("contact_id")]
        _hs("PUT", f"/crm/v3/lists/{args.list_id}/memberships/remove", token, ids)
        report["pruned"] = len(ids)
        _note(f"pruned {len(ids)} contacts who have not posted in "
              f"{args.keep_days}d")
    else:
        report["pruned"] = 0

    print(json.dumps(report, indent=2))
    return EXIT_OK


# --- post -----------------------------------------------------------------

def post(args) -> int:
    token = _token()
    client = UnipileClient()
    items = json.load(open(args.input) if args.input != "-" else sys.stdin)
    if isinstance(items, dict):
        items = items.get("candidates", [])

    drafted = [i for i in items if (i.get("comment") or "").strip()]
    out = {"posted": [], "rejected": [], "dry_run": args.dry_run}

    # Re-check everything at write time — see the module docstring.
    if not within_active_hours(cfg.ACTIVE_HOURS):
        out["rejected"] = [{**i, "reason": "outside active hours"} for i in drafted]
        print(json.dumps(out, indent=2))
        return EXIT_HALT

    today, recent, ever = ledger_counts(token)
    day_start, day_end = chicago_day_bounds()
    independent = client.comments_today(cfg.SHAWN_PROVIDER_ID, day_start, day_end)
    decision = decide_allowance(
        posted_today=today, per_day=cfg.COMMENTS_PER_DAY,
        per_run=cfg.COMMENTS_PER_RUN,
        ledger_writes_in_window=recent, ledger_writes_ever=ever,
        independent_count=independent,
    )
    out["cap"] = {"posted_today": today, "independent_count": independent,
                  "allowance": decision.allowance, "reason": decision.reason}
    if decision.halted or decision.allowance == 0:
        out["rejected"] = [{**i, "reason": f"cap: {decision.reason}"} for i in drafted]
        print(json.dumps(out, indent=2))
        return EXIT_HALT if decision.halted else EXIT_OK

    already = commented_post_ids(client.self_comments(cfg.SHAWN_PROVIDER_ID))

    for item in drafted[:decision.allowance]:
        text = item["comment"].strip()
        social = item.get("post_social_id") or ""
        key = social.rsplit(":", 1)[-1]

        if key in already:
            out["rejected"].append({**item, "reason": "already commented (re-checked at write time)"})
            continue
        if len(text) > COMMENT_MAX_CHARS:
            out["rejected"].append({**item, "reason": f"{len(text)} chars over the {COMMENT_MAX_CHARS} limit"})
            continue
        if not within_active_hours(cfg.ACTIVE_HOURS):
            out["rejected"].append({**item, "reason": "active-hours window closed mid-run"})
            continue

        if args.dry_run:
            out["posted"].append({**item, "dry_run": True,
                                  "would_post_as": cfg.SHAWN_ACCOUNT_ID})
            continue

        try:
            resp = client.post_comment(social, text)
        except (UnipileError, PermissionError) as exc:
            out["rejected"].append({**item, "reason": f"post failed: {exc}"})
            verdict = getattr(exc, "verdict", None)
            if verdict and verdict.action in (Action.HALT, Action.STOP_FOR_DAY):
                out["halted"] = str(exc)
                break
            continue

        # Log only a verified send. post_comment already refused anything
        # that was not CommentSent.
        task_id = log_comment(token, item["contact_id"], item.get("post_url", ""),
                              text, resp.get("comment_id"))
        already.add(key)
        out["posted"].append({**item, "comment_id": resp.get("comment_id"),
                              "ledger_task_id": task_id})
        time.sleep(random.uniform(90, 180))

    print(json.dumps(out, indent=2))
    return EXIT_OK


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan", help="emit eligible posts; writes nothing")
    p.add_argument("--list-id", default="8308")
    p.add_argument("--limit", type=int)
    p.add_argument("--max-seconds", type=int, default=420,
                   help="stop and report a partial result rather than be "
                        "killed by an external timeout")
    p.set_defaults(fn=plan)
    sc = sub.add_parser("scan", help="measure who actually posts; writes nothing")
    sc.add_argument("--list-id", default="8308")
    sc.add_argument("--limit", type=int)
    sc.add_argument("--keep-days", type=int, default=90,
                    help="a contact whose newest original post is older than "
                         "this is dead weight on the roster")
    sc.add_argument("--prune", action="store_true",
                    help="actually remove them from the list")
    sc.set_defaults(fn=scan)
    pr = sub.add_parser("prune", help="apply a scan report to list membership")
    pr.add_argument("--input", required=True, help="a scan report JSON")
    pr.add_argument("--list-id", default="8308")
    pr.add_argument("--keep-days", type=int, default=90)
    pr.add_argument("--dry-run", action="store_true")
    pr.set_defaults(fn=prune_from)
    w = sub.add_parser("post", help="publish drafted comments")
    w.add_argument("--input", required=True, help="JSON file, or - for stdin")
    w.add_argument("--dry-run", action="store_true")
    w.set_defaults(fn=post)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
