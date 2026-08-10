#!/usr/bin/env python3
"""Shared HubSpot REST helpers for the partner/M&A scripts.

Every script in here talks to the same portal with the same retry and paging
rules; keeping one copy means a fix to rate-limit handling lands everywhere at
once instead of drifting between six near-identical helpers.

The token comes from QBS_HUBSPOT_TOKEN in the environment - never from a file in
this repo.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.hubapi.com"

# HubSpot's 429 carries no Retry-After, so back off geometrically and cap it.
RETRY_CODES = frozenset({429, 500, 502, 503, 504})


class HubSpotError(RuntimeError):
    def __init__(self, code: int, path: str, body: str) -> None:
        super().__init__(f"HTTP {code} {path}: {body}")
        self.code = code
        self.path = path
        self.body = body


def token() -> str:
    tok = os.environ.get("QBS_HUBSPOT_TOKEN", "").strip()
    if not tok:
        raise HubSpotError(0, "-", "set QBS_HUBSPOT_TOKEN")
    return tok


def call(path: str, payload=None, method: str | None = None, tries: int = 6):
    if method is None:
        method = "GET" if payload is None else "POST"
    data = json.dumps(payload).encode() if payload is not None else None
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request(
            f"{API}{path}", data=data, method=method,
            headers={"Authorization": f"Bearer {token()}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            last = exc.read().decode()[:500]
            if exc.code in RETRY_CODES:
                time.sleep(min(2 ** attempt, 20))
                continue
            raise HubSpotError(exc.code, path, last) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last = str(exc)
            time.sleep(min(2 ** attempt, 20))
    raise HubSpotError(0, path, f"gave up after {tries}: {last}")


def properties(obj: str) -> list[dict]:
    return call(f"/crm/v3/properties/{obj}").get("results", [])


def search_all(obj: str, body: dict, page_limit: int = 100) -> list[dict]:
    """Page a CRM search to exhaustion.

    Note HubSpot's search endpoint stops at 10,000 records however you page it;
    callers that need the whole object must use the list endpoint instead.
    """
    out, after = [], None
    body = dict(body, limit=page_limit)
    while True:
        if after:
            body["after"] = after
        page = call(f"/crm/v3/objects/{obj}/search", body)
        out.extend(page.get("results", []))
        after = page.get("paging", {}).get("next", {}).get("after")
        if not after:
            return out
        time.sleep(0.1)


def batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main() -> None:
    """Print the contact/company properties this project cares about."""
    interest = ("linkedin", "zoominfo", "ma_", "_ma", "partner", "jobtitle",
                "email", "acquisition", "hublead")
    for obj in ("contacts", "companies"):
        print(f"\n=== {obj} ===")
        for p in sorted(properties(obj), key=lambda p: p["name"]):
            n = p["name"]
            if not any(k in n for k in interest):
                continue
            flags = []
            if p.get("hasUniqueValue"):
                flags.append("UNIQUE")
            if p.get("hidden"):
                flags.append("hidden")
            if p.get("calculated"):
                flags.append("calculated")
            opts = [o["value"] for o in (p.get("options") or [])][:8]
            print(f"  {n:46s} {p['type']:14s} "
                  f"{','.join(flags):22s} {p.get('label','')[:34]}"
                  + (f"  opts={opts}" if opts else ""))


if __name__ == "__main__":
    main()
