"""Version-tolerant Unipile transport: v2 preferred, v1 as fallback.

WHY A FALLBACK RATHER THAN A MIGRATION
--------------------------------------
v2 is better in every way that matters -- a clean host on standard 443, no
port workaround, Sales Navigator working where v1 returns 401, and honest
per-feature health in ``products_connection_status`` where v1's
``sources[].status`` reports OK while a feature is dead.

But v2 is **BETA** and Unipile warns of breaking changes, and an unattended
daily routine is the worst place to discover one. v1 is proven: it wrote 56
provider IDs unattended on 2026-08-30, and 195 tests are written against its
shapes.

So this tries v2 first and falls back to v1 automatically. A v2 outage
degrades the run instead of ending it, and the caller never learns which
answered. This is the same shape as
``contact-verification/scripts/unipile.py``: probe candidates, first working
one wins, halt only when none does.

THE TWO PATHS
-------------
    v2   https://api.unipile.com/v2/{acc_id}/users/{id}
         account id in the PATH; plain 443; needs UNIPILE_V2_API_KEY
    v1   https://api30.unipile.com/api/v1/users/{id}?account_id=..&port=16072
         account id as a QUERY param; tenant port moved to ?port= because
         this environment's egress reaches 443 only

SHAPE DIFFERENCES THIS MODULE HIDES
-----------------------------------
    envelope    v1 "items"      v2 "data"
    timestamp   v1 "date"       v2 "created_at"
    post id     v1 "social_id" ("urn:li:activity:123")
                v2 base64 composite decoding to BOTH urns:
                   ["activity:7496280276944269313","ugcPost:7496280276105441280"]

Callers get v1-shaped dicts regardless, so `posts.py`, `verify.py` and the
existing tests keep working unchanged.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .unipile import Unipile, UnipileError

V2_BASE = "https://api.unipile.com/v2"

#: Shawn's v2 account. Maps to legacy v1 id 7lBoyXuETqKdiJYLj5HBGA.
V2_ACCOUNT_ID = "acc_01m19mb99wfzvsb68etkn5n87x"


def decode_v2_post_id(post_id: str | None) -> dict[str, str]:
    """Unpack a v2 post id into its constituent URNs.

    v2 replaced `social_id` with a base64 composite carrying BOTH urns::

        WyJhY3Rpdml0eTo3NDk2Li4uIiwidWdjUG9zdDo3NDk2Li4uIl0=
          -> ["activity:7496280276944269313","ugcPost:7496280276105441280"]

    That looks deliberate: under v1, `Comment.post_id` matched the numeric tail
    of `social_id` rather than the post's own `id`, so joining on `id` silently
    failed for every ugcPost. Carrying both removes the ambiguity.
    """
    if not post_id:
        return {}
    try:
        padded = post_id + "=" * (-len(post_id) % 4)
        parts = json.loads(base64.b64decode(padded).decode())
    except Exception:
        return {}
    out: dict[str, str] = {}
    for part in parts if isinstance(parts, list) else []:
        kind, _, num = str(part).partition(":")
        if kind and num:
            out[kind] = num
    return out


def v2_post_to_v1(post: dict) -> dict:
    """Reshape a v2 post so v1-era code reads it unchanged."""
    urns = decode_v2_post_id(post.get("id"))
    # Prefer activity, which is what v1's social_id carried for most posts.
    kind = "activity" if "activity" in urns else next(iter(urns), None)
    social_id = f"urn:li:{kind}:{urns[kind]}" if kind else None

    shaped = dict(post)
    shaped["social_id"] = social_id
    shaped["parsed_datetime"] = post.get("created_at") or post.get("parsed_datetime")
    shaped["comment_counter"] = post.get("comments_counter", post.get("comment_counter"))
    shaped["reaction_counter"] = post.get("reactions_counter", post.get("reaction_counter"))
    # Every urn v2 gave us, so dedupe can match on any of them.
    shaped["_all_urn_ids"] = list(urns.values())
    return shaped


def v2_comment_to_v1(comment: dict) -> dict:
    """Reshape a v2 comment so `commented_post_ids` reads it unchanged."""
    shaped = dict(comment)
    shaped["date"] = comment.get("created_at") or comment.get("date")
    if "post_id" not in shaped:
        urns = decode_v2_post_id(comment.get("post"))
        if urns:
            shaped["post_id"] = next(iter(urns.values()))
    return shaped


@dataclass
class Route:
    version: str
    reason: str


class UnipileClient:
    """Try v2, fall back to v1. Callers never see the difference."""

    def __init__(
        self,
        v2_key: str | None = None,
        v1_key: str | None = None,
        v2_account: str = V2_ACCOUNT_ID,
        prefer: str = "v2",
    ):
        self.v2_key = v2_key or os.environ.get("UNIPILE_V2_API_KEY", "").strip()
        self.v2_account = os.environ.get("UNIPILE_V2_ACCOUNT_ID", v2_account).strip()
        self.prefer = prefer
        self._v1: Unipile | None = None
        self._v1_key = v1_key
        #: Set after the first successful call, for the run report. A routine
        #: must say which path served it -- silently degrading to v1 without
        #: reporting it is how a version problem stays invisible.
        self.route: Route | None = None

    @property
    def v1(self) -> Unipile:
        if self._v1 is None:
            self._v1 = Unipile(api_key=self._v1_key)
        return self._v1

    # --- v2 primitives ----------------------------------------------------

    def _v2_get(self, path: str, params: dict | None = None) -> dict:
        if not self.v2_key:
            raise UnipileError("no v2 key configured")
        url = f"{V2_BASE}/{self.v2_account}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url, headers={"X-API-KEY": self.v2_key, "accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read() or b"{}")

    def _try(self, v2_call, v1_call, label: str):
        """Run the v2 path, fall back to v1, record which answered."""
        if self.prefer == "v2" and self.v2_key:
            try:
                result = v2_call()
                self.route = Route("v2", "primary")
                return result
            except Exception as exc:
                self.route = Route("v1", f"v2 failed on {label}: {exc}")
        elif not self.v2_key:
            self.route = Route("v1", "no v2 key configured")
        else:
            self.route = Route("v1", "v1 preferred by caller")
        return v1_call()

    # --- the calls both programs make ------------------------------------

    def profile(self, identifier: str) -> dict:
        """Profile WITH dated experience rows. **v1 ONLY — deliberately.**

        Measured 2026-08-30: v2's profile endpoint does not return work
        experience at all. Six parameter variants (linkedin_sections,
        sections, include, *) all returned HTTP 200 with zero rows and no
        experience-shaped key anywhere in the payload. `specifics` carries
        `throttled_sections: []`, so the mechanism may exist and simply not be
        wired up during beta.

        This is the one call that must NOT fall back the other way. A v2
        profile looks perfectly healthy and is missing the only field the
        Reading Rule reads -- exactly the shape that writes "No Longer with
        Company" across the CRM. verify.read_roles raises InstrumentError on
        it (and did, during this migration), but the correct fix is not to
        ask v2 for it at all.

        Revisit when Unipile documents experience on v2.
        """
        self.route = Route("v1", "v2 does not return work_experience")
        return self.v1.profile(identifier)

    def posts(self, provider_id: str, limit: int = 10) -> list[dict]:
        def _v2():
            d = self._v2_get(f"/users/{provider_id}/posts", {"limit": limit})
            return [v2_post_to_v1(p) for p in (d.get("data") or [])]

        def _v1():
            return (self.v1.posts(provider_id, limit) or {}).get("items", [])

        return self._try(_v2, _v1, "posts")

    def self_comments(self, provider_id: str, limit: int = 100) -> list[dict]:
        """Every comment, paged to the end on either version.

        Fully paged on purpose: a partial dedupe set silently re-comments on
        older posts while looking authoritative.
        """
        def _v2():
            items, cursor = [], None
            while True:
                params = {"limit": limit}
                if cursor:
                    params["cursor"] = cursor
                d = self._v2_get(f"/users/{provider_id}/comments", params)
                items += [v2_comment_to_v1(c) for c in (d.get("data") or [])]
                cursor = d.get("cursor")
                if not cursor:
                    return items

        return self._try(_v2, lambda: self.v1.self_comments(provider_id, limit),
                         "self_comments")

    def health(self) -> dict:
        """Per-feature connection status.

        **v2 preferred here** -- this is where v2 is strictly better. It
        reports `products_connection_status` (classic / company /
        sales_navigator), the honest signal. v1 only reports MESSAGING and
        says OK while Sales Navigator is dead, which is exactly how that went
        undiagnosed. When answering from v1, say so rather than implying the
        stronger check ran.
        """
        if self.v2_key:
            try:
                # Account detail is /v2/accounts/{id}, NOT /v2/{id} — the
                # account id is only a path prefix on per-account resources.
                import urllib.request as _u
                req = _u.Request(f"{V2_BASE}/accounts/{self.v2_account}",
                                 headers={"X-API-KEY": self.v2_key,
                                          "accept": "application/json"})
                with _u.urlopen(req, timeout=60) as resp:
                    d = json.loads(resp.read() or b"{}")
                meta = (d.get("metadata") or {})
                self.route = Route("v2", "primary")
                return {
                    "source": "v2/products_connection_status",
                    "products": meta.get("products_connection_status") or {},
                    "status": d.get("status"),
                    "is_locked": d.get("is_locked"),
                }
            except Exception as exc:
                self.route = Route("v1", f"v2 health failed: {exc}")

        data = self.v1.accounts()
        for a in data.get("items", []):
            if a.get("id") == self.v1.account_id:
                return {
                    "source": "v1/sources (MESSAGING only — does NOT reflect "
                              "Sales Navigator or company-page health)",
                    "products": {s.get("id", "").split("_")[-1].lower(): s.get("status")
                                 for s in a.get("sources", [])},
                    "status": None,
                    "is_locked": None,
                }
        raise UnipileError("account not found on either version")
