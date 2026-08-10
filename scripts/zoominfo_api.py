#!/usr/bin/env python3
"""Minimal ZoomInfo Enterprise API client (PKI/JWT auth).

Why this exists: the ZoomInfo MCP connector is fine for a handful of lookups but
sourcing decision-makers for ~1,400 partner companies needs a few hundred
sequential calls. Driving the REST API from a script does that unattended.

Credentials come from the environment only - never commit or write them to the
repo:

    ZI_USERNAME     ZoomInfo login (the API-enabled user)
    ZI_CLIENT_ID    API client id issued with the PKI key pair
    ZI_PRIVATE_KEY  the private key, PEM or bare base64, OR
    ZI_PRIVATE_KEY_FILE  path to a file holding either form

The access token lasts an hour, so it is cached in memory and re-minted lazily.
"""

from __future__ import annotations

import base64
import json
import os
import textwrap
import time
import urllib.error
import urllib.request

BASE = "https://api.zoominfo.com"
AUTH_URL = f"{BASE}/authenticate"

# ZoomInfo's PKI flow: we sign our own short-lived JWT with the private key and
# trade it for a one-hour access token. These two claims are fixed by ZoomInfo.
JWT_AUDIENCE = "enterprise_api"
JWT_ISSUER = "api-client@zoominfo.com"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")


class ZoomInfoError(RuntimeError):
    pass


def _normalize_pem(value: str) -> str:
    """Accept a real PEM, a PEM flattened onto one line, or bare base64.

    Keys get pasted around as a single line often enough that requiring
    well-formed PEM here just turns a working key into a confusing parse error.
    """
    v = (value or "").strip()
    if not v:
        raise ZoomInfoError("empty private key")
    body = v
    for marker in ("-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----",
                   "-----BEGIN RSA PRIVATE KEY-----",
                   "-----END RSA PRIVATE KEY-----"):
        body = body.replace(marker, " ")
    body = "".join(body.split())
    label = "RSA PRIVATE KEY" if "BEGIN RSA PRIVATE KEY" in v else "PRIVATE KEY"
    try:
        base64.b64decode(body, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise ZoomInfoError(f"private key is not valid base64: {exc}") from exc
    return (f"-----BEGIN {label}-----\n"
            + "\n".join(textwrap.wrap(body, 64))
            + f"\n-----END {label}-----\n")


def _load_private_key() -> str:
    path = os.environ.get("ZI_PRIVATE_KEY_FILE", "")
    if path:
        with open(path, encoding="utf-8") as fh:
            return _normalize_pem(fh.read())
    return _normalize_pem(os.environ.get("ZI_PRIVATE_KEY", ""))


def _post(url: str, body: dict | None, token: str | None = None,
          tries: int = 6) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    # api.zoominfo.com sits behind Cloudflare, which 403s the default
    # "Python-urllib/x.y" agent outright (error 1010, browser_signature_banned).
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            last = exc.read().decode()[:400]
            # 429 = rate limit, 5xx = transient. Everything else is our bug and
            # retrying just hides it.
            if exc.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** attempt, 30))
                continue
            raise ZoomInfoError(f"HTTP {exc.code} {url}: {last}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last = str(exc)
            time.sleep(min(2 ** attempt, 30))
    raise ZoomInfoError(f"gave up on {url}: {last}")


class ZoomInfo:
    def __init__(self) -> None:
        self.username = os.environ.get("ZI_USERNAME", "").strip()
        self.client_id = os.environ.get("ZI_CLIENT_ID", "").strip()
        self.private_key = _load_private_key()
        if not self.username:
            raise ZoomInfoError("set ZI_USERNAME")
        self._token = ""
        self._expires = 0.0

    # ---------------------------------------------------------------- auth
    def _mint_jwt(self) -> str:
        import jwt  # imported lazily so --help works without the dependency

        now = int(time.time())
        claims = {
            "aud": JWT_AUDIENCE,
            "iss": JWT_ISSUER,
            "username": self.username,
            "iat": now,
            "exp": now + 300,
        }
        if self.client_id:
            claims["clientId"] = self.client_id
        return jwt.encode(claims, self.private_key, algorithm="RS256")

    @property
    def token(self) -> str:
        # Access tokens live an hour; renew a minute early to avoid racing it.
        if self._token and time.time() < self._expires - 60:
            return self._token
        signed = self._mint_jwt()
        res = _post(AUTH_URL, None, token=signed)
        tok = res.get("jwt") or res.get("token") or ""
        if not tok:
            raise ZoomInfoError(f"no token in auth response: {res}")
        self._token, self._expires = tok, time.time() + 3600
        return tok

    # ------------------------------------------------------------- queries
    def call(self, path: str, body: dict) -> dict:
        return _post(f"{BASE}{path}", body, token=self.token)

    def search_contacts(self, **kw) -> dict:
        return self.call("/search/contact", kw)

    def enrich_contacts(self, inputs: list[dict], fields: list[str]) -> dict:
        return self.call("/enrich/contact",
                         {"matchPersonInput": inputs, "outputFields": fields})

    def enrich_companies(self, inputs: list[dict], fields: list[str]) -> dict:
        return self.call("/enrich/company",
                         {"matchCompanyInput": inputs, "outputFields": fields})


def main() -> int:
    """Smoke-test authentication and report exactly what is missing."""
    try:
        zi = ZoomInfo()
    except ZoomInfoError as exc:
        print(f"config error: {exc}")
        return 2
    print(f"username  {zi.username}")
    print(f"client_id {zi.client_id or '(not set)'}")
    try:
        tok = zi.token
    except ZoomInfoError as exc:
        print(f"AUTH FAILED: {exc}")
        return 1
    print(f"AUTH OK, token {len(tok)} chars")
    res = zi.search_contacts(companyWebsite="hubspot.com",
                             managementLevel="C Level Exec", rpp=1, page=1)
    print(f"probe search: maxResults={res.get('maxResults')} "
          f"returned={len(res.get('data') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
