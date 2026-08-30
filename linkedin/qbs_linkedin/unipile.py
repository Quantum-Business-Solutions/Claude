"""Unipile transport that works from a cloud container.

THE FIX, and why it matters
---------------------------
Unipile assigns a tenant DSN on a non-standard port -- ours is
``api30.unipile.com:16072``. This environment's egress policy permits outbound
HTTPS on **443 only**, so that DSN is unreachable: a direct socket to
:16072 times out while :443 on the same IP is open.

That forced every LinkedIn call through the Unipile MCP connector, and
routine-fired sessions carry no connectors at all (measured 2026-08-30 --
a broad search for ``mcp__`` in a fired session returned nothing). So the
schedule could never touch LinkedIn, and both programs halted every run while
reporting SUCCEEDED.

**Unipile supports this case directly.** Move the port out of the host and
into a query parameter, and the call goes over standard 443:

    https://api30.unipile.com:16072/api/v1/accounts     -> connection reset
    https://api30.unipile.com/api/v1/accounts?port=16072 -> HTTP 200

Verified live for every endpoint the routines need: ``/accounts``,
``/users/{id}`` with ``linkedin_sections=experience``, ``/users/{id}/comments``
and ``/users/{id}/posts``. No MCP, no connector grant, no support ticket --
just the API key already sitting in the environment.

Docs: https://developer.unipile.com/docs/api-usage
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import (
    PROFILE_SECTIONS_PARAM,
    SHAWN_ACCOUNT_ID,
    assert_send_account,
)
from .errors import Action, Verdict, classify

DEFAULT_DSN = "api30.unipile.com:16072"


class UnipileError(RuntimeError):
    """A call failed in a way the caller must not paper over."""

    def __init__(self, message: str, verdict: Verdict | None = None):
        super().__init__(message)
        self.verdict = verdict


def split_dsn(dsn: str | None = None) -> tuple[str, str | None]:
    """Return (host, port) from a DSN in any of its written forms."""
    raw = (dsn or os.environ.get("UNIPILE_DSN") or DEFAULT_DSN).strip()
    raw = re.sub(r"^https?://", "", raw).rstrip("/")
    host, _, port = raw.partition(":")
    return host, (port or None)


def base_url(dsn: str | None = None) -> str:
    """Always the bare host on 443. The port travels as a query parameter."""
    host, _ = split_dsn(dsn)
    return f"https://{host}/api/v1"


class Unipile:
    """Read/write client for the Unipile LinkedIn API over port 443."""

    def __init__(
        self,
        api_key: str | None = None,
        dsn: str | None = None,
        account_id: str = SHAWN_ACCOUNT_ID,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.environ.get("UNIPILE_API_KEY", "").strip()
        if not self.api_key:
            raise UnipileError(
                "UNIPILE_API_KEY is not set. That is NOT the same as "
                "'LinkedIn could not be read' — do not record verdicts."
            )
        self.host, self.port = split_dsn(dsn)
        self.base = base_url(dsn)
        # Reads are scoped to Shawn; writes re-assert via assert_send_account.
        self.account_id = account_id
        self.timeout = timeout

    def _url(self, path: str, params: dict | None = None) -> str:
        query = dict(params or {})
        query.setdefault("account_id", self.account_id)
        # The whole point: the tenant port rides as a parameter so the
        # request itself goes to 443.
        if self.port:
            query["port"] = self.port
        return f"{self.base}{path}?{urllib.parse.urlencode(query)}"

    def get(self, path: str, params: dict | None = None, retries: int = 2) -> dict:
        """GET with the shared error taxonomy applied.

        A retryable fault is retried; anything else raises, because the
        alternative is a run that quietly records a fault as a finding.
        """
        url = self._url(path, params)
        req = urllib.request.Request(
            url, headers={"X-API-KEY": self.api_key, "accept": "application/json"}
        )
        last: Verdict | None = None
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = json.loads(resp.read() or b"{}")
            except urllib.error.HTTPError as exc:
                try:
                    payload = json.loads(exc.read() or b"{}")
                except Exception:
                    payload = {"status": exc.code, "type": "errors/unknown"}
            except Exception as exc:  # socket, DNS, TLS
                last = Verdict(Action.RETRY, f"{type(exc).__name__}: {exc}")
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise UnipileError(f"{path}: {last.reason}", last) from exc

            verdict = classify(payload)
            if verdict.action is Action.PROCEED:
                return payload
            last = verdict
            if verdict.action is Action.RETRY and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise UnipileError(f"{path}: {verdict.reason}", verdict)

        raise UnipileError(f"{path}: exhausted retries", last)

    # --- The calls the routines actually make ----------------------------

    def accounts(self) -> dict:
        return self.get("/accounts")

    def assert_identity(self, expected_provider_id: str) -> dict:
        """Confirm the sending account is who we think before anything writes.

        One API key spans seven accounts and five people. Member IDs are
        immutable; slugs are user-changeable, so the assertion is on the ID.
        """
        for account in self.accounts().get("items", []):
            if account.get("id") != self.account_id:
                continue
            im = (account.get("connection_params") or {}).get("im") or {}
            if im.get("id") != expected_provider_id:
                raise UnipileError(
                    f"account {self.account_id} has member id {im.get('id')}, "
                    f"expected {expected_provider_id} — refusing to act as "
                    "someone else"
                )
            return account
        raise UnipileError(f"account {self.account_id} not found on this key")

    def profile(self, identifier: str,
                sections: str = PROFILE_SECTIONS_PARAM) -> dict:
        """Fetch a profile WITH dated experience rows.

        `sections` is not optional in practice: omitting it returns HTTP 200
        with no work_experience key at all, and a parser that reads that as
        "no current role" writes 'No Longer with Company' across the CRM.
        """
        return self.get(f"/users/{identifier}", {"linkedin_sections": sections})

    def posts(self, provider_id: str, limit: int = 10) -> dict:
        """Recent posts. Requires the member id — a vanity slug returns 422."""
        return self.get(f"/users/{provider_id}/posts", {"limit": limit})

    def self_comments(self, provider_id: str, limit: int = 100) -> list[dict]:
        """Every comment Shawn has made, across all posts, paged to the end.

        Paged fully on purpose: a partial set silently re-comments on older
        posts, and looks authoritative while doing it.
        """
        items: list[dict] = []
        cursor = None
        while True:
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            page = self.get(f"/users/{provider_id}/comments", params)
            items += page.get("items", [])
            cursor = page.get("cursor")
            if not cursor:
                return items

    def post_comment(self, post_social_id: str, text: str) -> dict:
        """Post a comment. The only write this client performs."""
        assert_send_account(self.account_id)
        url = self._url(f"/posts/{urllib.parse.quote(post_social_id, safe='')}/comments")
        body = urllib.parse.urlencode({"text": text}).encode()
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={
                "X-API-KEY": self.api_key,
                "accept": "application/json",
                "content-type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read() or b"{}")
            except Exception:
                payload = {"status": exc.code, "type": "errors/unknown"}

        verdict = classify(payload)
        if verdict.action is not Action.PROCEED:
            raise UnipileError(f"comment on {post_social_id}: {verdict.reason}", verdict)
        return payload


def probe(dsn: str | None = None) -> str:
    """Human-readable reachability report. Used by preflight."""
    host, port = split_dsn(dsn)
    lines = [f"host {host}, tenant port {port or '(none)'}"]
    try:
        client = Unipile(dsn=dsn)
        data = client.accounts()
        lines.append(
            f"  REACHABLE over 443 with ?port={port} — "
            f"{data.get('total_count')} account(s)"
        )
    except UnipileError as exc:
        lines.append(f"  FAILED: {exc}")
    return "\n".join(lines)
