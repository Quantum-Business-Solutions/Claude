#!/usr/bin/env python3
"""Preflight for the QBS LinkedIn routines.

Modelled on contact-verification/scripts/preflight.py: run it before anything
else, stop the run on any non-zero exit, and never "try anyway".

    exit 0  all checks passed
    exit 2  environment / auth / data fault
    exit 3  schema drift or a stale code assumption

The distinction matters. Exit 2 means fix the environment and re-run. Exit 3
means the portal changed under the code and a human must reconcile the two
before any run is trusted.

This covers HubSpot only. Unipile lives behind a non-443 port that the agent
proxy does not carry, so its self-test is a separate MANDATORY step the
routine performs through the Unipile MCP -- read one profile known to have
dated experience rows, and HALT if they are absent. Without that, every
contact scores unreadable and the run reports an instrument failure as a
finding about the prospects.

Usage:
    QBS_HUBSPOT_TOKEN=pat-... python3 scripts/preflight.py [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qbs_linkedin import config as cfg  # noqa: E402
from qbs_linkedin.ledger import (  # noqa: E402
    LEDGER_STALE_DAYS,
    chicago_day_bounds,
    decide_allowance,
)

EXIT_OK, EXIT_ENV, EXIT_SCHEMA = 0, 2, 3
API = "https://api.hubapi.com"

@dataclass
class Report:
    checks: list[dict] = field(default_factory=list)
    exit_code: int = EXIT_OK

    def add(self, name: str, ok: bool, detail: str, fatal: int | None = None) -> bool:
        self.checks.append({"check": name, "ok": ok, "detail": detail})
        if not ok and fatal:
            self.exit_code = max(self.exit_code, fatal)
        return ok

    def render(self) -> str:
        lines = []
        for c in self.checks:
            mark = "PASS" if c["ok"] else "FAIL"
            lines.append(f"  [{mark}] {c['check']}: {c['detail']}")
        verdict = {
            EXIT_OK: "PREFLIGHT OK",
            EXIT_ENV: "PREFLIGHT FAILED (exit 2 - environment/auth/data)",
            EXIT_SCHEMA: "PREFLIGHT FAILED (exit 3 - schema drift)",
        }[self.exit_code]
        return "\n".join(lines) + f"\n\n{verdict}"


def _post(path: str, token: str, body: dict) -> dict:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        API + path, headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _count(token: str, obj: str, filters: list[dict]) -> int:
    """Return the search API's exact `total`.

    Never len(results): with page_size at a cap value a count silently
    saturates at the ceiling instead of reporting the real number.
    """
    return _post(f"/crm/v3/objects/{obj}/search", token,
                 {"filterGroups": [{"filters": filters}], "limit": 1}).get("total", 0)


def check_auth(token: str, rep: Report) -> bool:
    try:
        info = _post("/oauth/v2/private-apps/get/access-token-info", token,
                     {"tokenKey": token})
    except urllib.error.HTTPError as exc:
        return rep.add("auth", False, f"HTTP {exc.code} from HubSpot", EXIT_ENV)
    except Exception as exc:  # network, DNS, proxy
        return rep.add("auth", False, f"unreachable: {exc}", EXIT_ENV)

    hub = str(info.get("hubId"))
    if hub != cfg.HUBSPOT_PORTAL_ID:
        return rep.add("auth", False,
                       f"token is for portal {hub}, expected {cfg.HUBSPOT_PORTAL_ID} "
                       "- refusing to operate on the wrong portal", EXIT_ENV)
    scopes = set(info.get("scopes") or [])
    needed = {
        "crm.objects.contacts.read", "crm.objects.contacts.write",
        "crm.objects.companies.read", "crm.lists.read", "crm.objects.owners.read",
    }
    missing = needed - scopes
    if missing:
        return rep.add("auth", False, f"token missing scopes: {sorted(missing)}", EXIT_ENV)
    return rep.add("auth", True, f"portal {hub}, {len(scopes)} scopes")


def check_property_schema(token: str, rep: Report) -> None:
    """Every property the code names must exist with the assumed shape."""
    try:
        props = {p["name"]: p for p in
                 _get("/crm/v3/properties/contacts", token).get("results", [])}
        tasks = {p["name"]: p for p in
                 _get("/crm/v3/properties/tasks", token).get("results", [])}
    except Exception as exc:
        rep.add("schema.fetch", False, f"could not read schema: {exc}", EXIT_ENV)
        return

    required = [
        cfg.UPSERT_KEY_PROPERTY, cfg.SECONDARY_MATCH_PROPERTY,
        cfg.AI_STILL_AT_COMPANY, cfg.AI_CONTACT_EVIDENCE, cfg.AI_VERIFIED_DATE,
        cfg.AI_LAST_ATTEMPT_DATE, cfg.AI_SOURCES_CONFIRMING, cfg.AI_JOB_TITLE,
        cfg.LAST_MESSAGE_SENT, cfg.LAST_INVITE_SENT,
        "hs_lead_status", "hs_seniority", "firstname", "lastname",
    ]
    missing = [p for p in required if p not in props]
    rep.add("schema.contacts", not missing,
            "all present" if not missing else f"missing: {missing}",
            EXIT_SCHEMA)

    # The upsert key must still be unique, or every roster write duplicates.
    key = props.get(cfg.UPSERT_KEY_PROPERTY)
    if key is not None:
        rep.add("schema.upsert_key_unique", bool(key.get("hasUniqueValue")),
                f"{cfg.UPSERT_KEY_PROPERTY} hasUniqueValue="
                f"{key.get('hasUniqueValue')}", EXIT_SCHEMA)

    # ai__sources_confirming is a NUMBER. The runbook instructs writing a
    # string label into it; that write fails or coerces to garbage.
    src = props.get(cfg.AI_SOURCES_CONFIRMING)
    if src is not None:
        rep.add("schema.sources_confirming_numeric", src.get("type") == "number",
                f"type={src.get('type')} (must be number - it is a COUNT, "
                "not a source label)", EXIT_SCHEMA)

    # Verdict vocabulary must match the live option set, or outreach writes
    # data the verification routine cannot compare against.
    verdict_prop = props.get(cfg.AI_STILL_AT_COMPANY)
    if verdict_prop is not None:
        live = {o["value"] for o in verdict_prop.get("options") or []}
        drift = set(cfg.VERDICTS) - live
        rep.add("schema.verdicts", not drift,
                f"live options {sorted(live)}"
                + (f" - code expects missing {sorted(drift)}" if drift else ""),
                EXIT_SCHEMA)

    # The lead-status VALUE (not label) must resolve. A bad enum value returns
    # zero rows silently, indistinguishable from an empty pool.
    lead = props.get("hs_lead_status")
    if lead is not None:
        values = {o["value"] for o in lead.get("options") or []}
        ok = cfg.REQUIRED_LEAD_STATUS in values
        rep.add("schema.lead_status", ok,
                f"{cfg.REQUIRED_LEAD_STATUS!r} "
                + ("resolves" if ok else
                   "NOT FOUND - a bad enum value returns 0 rows silently, "
                   "which looks exactly like an empty pool"),
                EXIT_SCHEMA)

    task_type = tasks.get("hs_task_type")
    if task_type is not None:
        values = {o["value"] for o in task_type.get("options") or []}
        drift = set(cfg.ALL_LINKEDIN_TASK_TYPES) - values
        rep.add("schema.task_types", not drift,
                "all present" if not drift else f"missing: {sorted(drift)}",
                EXIT_SCHEMA)


def check_pool(token: str, rep: Report) -> None:
    """The candidate pool must be non-empty, or the run has nothing to do."""
    try:
        qualified = _count(token, "contacts", [
            {"propertyName": "hs_lead_status", "operator": "EQ",
             "value": cfg.REQUIRED_LEAD_STATUS},
            {"propertyName": "hs_seniority", "operator": "IN",
             "values": sorted(cfg.SENIORITY_ALLOWED)},
            {"propertyName": cfg.UPSERT_KEY_PROPERTY, "operator": "HAS_PROPERTY"},
            {"propertyName": cfg.LAST_MESSAGE_SENT, "operator": "NOT_HAS_PROPERTY"},
            {"propertyName": cfg.AI_STILL_AT_COMPANY, "operator": "NEQ",
             "value": cfg.VERDICT_NO},
        ])
    except Exception as exc:
        rep.add("pool", False, f"query failed: {exc}", EXIT_ENV)
        return
    rep.add("pool", qualified >= cfg.OutreachThresholds().min_candidates,
            f"{qualified:,} qualified candidates", EXIT_ENV)


def check_ledger_alive(token: str, rep: Report) -> None:
    """The send ledger must be trustworthy, or no run may send.

    Delegates the decision to ledger.decide_allowance so preflight and the
    routines cannot drift apart on what "safe to send" means.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=LEDGER_STALE_DAYS)
    linkedin_task = [
        {"propertyName": "hs_task_type", "operator": "IN",
         "values": list(cfg.ALL_LINKEDIN_TASK_TYPES)},
        {"propertyName": "hubspot_owner_id", "operator": "EQ",
         "value": cfg.SHAWN_OWNER_ID},
    ]
    day_start, day_end = chicago_day_bounds()
    try:
        recent = _count(token, "tasks", linkedin_task + [
            {"propertyName": cfg.CAP_DATE_PROPERTY, "operator": "GTE",
             "value": int(cutoff.timestamp() * 1000)}])
        ever = _count(token, "tasks", linkedin_task)
        today = _count(token, "tasks", linkedin_task + [
            {"propertyName": cfg.CAP_DATE_PROPERTY, "operator": "BETWEEN",
             "value": day_start, "highValue": day_end}])
    except Exception as exc:
        rep.add("ledger", False, f"query failed: {exc}", EXIT_ENV)
        return

    caps = cfg.OutreachCaps()
    decision = decide_allowance(
        posted_today=today,
        per_day=caps.daily_stop,
        per_run=caps.target_high,
        ledger_writes_in_window=recent,
        ledger_writes_ever=ever,
    )
    rep.add(
        "ledger", not decision.halted,
        f"{today} today / {recent} in {LEDGER_STALE_DAYS}d / {ever:,} ever "
        f"-> {decision.reason}",
        EXIT_ENV if decision.halted else None,
    )


def check_watch_list(token: str, rep: Report) -> None:
    """Engagement cannot run without a roster. A 404 must be loud, not silent."""
    from urllib.parse import quote
    try:
        _get(f"/crm/v3/lists/object-type-id/0-1/name/"
             f"{quote(cfg.WATCH_LIST_NAME)}", token)
        rep.add("watch_list", True, f"{cfg.WATCH_LIST_NAME!r} exists")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            rep.add("watch_list", False,
                    f"{cfg.WATCH_LIST_NAME!r} does not exist - the engagement "
                    "routine has no roster and must not run", EXIT_ENV)
        else:
            rep.add("watch_list", False, f"HTTP {exc.code}", EXIT_ENV)
    except Exception as exc:
        rep.add("watch_list", False, str(exc), EXIT_ENV)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--skip-watch-list", action="store_true",
                    help="outreach-only runs do not need the engagement roster")
    args = ap.parse_args()

    rep = Report()
    token = os.environ.get("QBS_HUBSPOT_TOKEN", "").strip()
    if not token:
        rep.add("env", False,
                "QBS_HUBSPOT_TOKEN unset - set it on the Claude Code "
                "environment so scheduled routines inherit it", EXIT_ENV)
    elif check_auth(token, rep):
        check_property_schema(token, rep)
        check_pool(token, rep)
        check_ledger_alive(token, rep)
        if not args.skip_watch_list:
            check_watch_list(token, rep)

    if args.json:
        print(json.dumps({"exit_code": rep.exit_code, "checks": rep.checks}, indent=2))
    else:
        print(rep.render())
    return rep.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
