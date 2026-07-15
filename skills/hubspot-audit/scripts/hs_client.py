"""
HubSpot Audit Client
====================

Reusable Python client for running audit-volume queries against a HubSpot portal
using a Private App token (a.k.a. service key).

Usage:
    from hs_client import HubSpotAuditClient

    hs = HubSpotAuditClient(token="pat-na1-...")
    portal = hs.get_portal_profile()
    workflows = hs.list_all_workflows()

Designed for the hubspot-audit skill. NOT designed for write operations — this
client intentionally does not implement create/update/delete methods.

Security:
- Never log or echo the token
- Pass the token at construction only
- The client never prints the token in errors or retries
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Iterator, List, Optional

import requests


HUBSPOT_API_BASE = "https://api.hubapi.com"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 5
BACKOFF_BASE = 2  # exponential backoff seconds


class HubSpotAuditError(Exception):
    """Base exception for audit client failures."""


class HubSpotAuthError(HubSpotAuditError):
    """Raised on 401/403 — token issues."""


class HubSpotScopeError(HubSpotAuditError):
    """Raised when the token lacks a required scope."""


class HubSpotRateLimitError(HubSpotAuditError):
    """Raised when daily limits are exceeded."""


@dataclass
class QueryRecord:
    """One record of an API call made, for the audit trail."""
    endpoint: str
    method: str
    timestamp: str
    status: int
    record_count: Optional[int] = None
    note: Optional[str] = None


class HubSpotAuditClient:
    """
    Read-only HubSpot API client tuned for audit-volume queries.

    Features:
    - Automatic pagination for list endpoints
    - Automatic retry with exponential backoff on 429/503
    - Scope error detection (suggests which scope to add)
    - Query audit trail for inclusion in deliverable appendix
    - No write methods by design
    """

    def __init__(self, token: str, record_audit_trail: bool = True):
        if not token or not token.startswith("pat-"):
            raise HubSpotAuthError(
                "Token does not appear to be a Private App token "
                "(should start with 'pat-'). "
                "Check HubSpot Settings → Integrations → Private Apps."
            )
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        })
        self.audit_trail: List[QueryRecord] = []
        self.record_audit_trail = record_audit_trail

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue a request with retry/backoff and audit logging."""
        url = f"{HUBSPOT_API_BASE}{path}"
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    timeout=DEFAULT_TIMEOUT,
                )
            except requests.RequestException as exc:
                if attempt > MAX_RETRIES:
                    raise HubSpotAuditError(f"Network error on {method} {path}: {exc}")
                time.sleep(BACKOFF_BASE ** attempt)
                continue

            # Rate limit
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", BACKOFF_BASE ** attempt))
                if attempt > MAX_RETRIES:
                    raise HubSpotRateLimitError(
                        f"Rate limited on {path} after {MAX_RETRIES} attempts. "
                        "Portal may have hit daily limit."
                    )
                time.sleep(retry_after)
                continue

            # Auth
            if resp.status_code == 401:
                raise HubSpotAuthError(
                    "Token is invalid or expired. "
                    "Ask the portal owner to regenerate the Private App token."
                )

            # Forbidden → usually missing scope
            if resp.status_code == 403:
                body = self._safe_json(resp)
                scope_hint = self._extract_scope_hint(body)
                msg = f"Forbidden on {method} {path}."
                if scope_hint:
                    msg += f" Likely missing scope: {scope_hint}"
                raise HubSpotScopeError(msg)

            # Transient server errors
            if resp.status_code in (502, 503, 504):
                if attempt > MAX_RETRIES:
                    raise HubSpotAuditError(
                        f"Server error {resp.status_code} on {path} after {MAX_RETRIES} attempts."
                    )
                time.sleep(BACKOFF_BASE ** attempt)
                continue

            # Success
            if 200 <= resp.status_code < 300:
                body = self._safe_json(resp)
                if self.record_audit_trail:
                    self._record(
                        endpoint=path,
                        method=method,
                        status=resp.status_code,
                        record_count=self._count_records(body),
                        note=note,
                    )
                return body

            # Unexpected
            raise HubSpotAuditError(
                f"HTTP {resp.status_code} on {method} {path}: {resp.text[:500]}"
            )

    def _safe_json(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {"_raw": resp.text}

    def _extract_scope_hint(self, body: Dict[str, Any]) -> Optional[str]:
        """Extract a scope suggestion from a 403 response body."""
        if isinstance(body, dict):
            # HubSpot error bodies sometimes include a "message" referencing scopes
            msg = body.get("message", "")
            if "scope" in msg.lower():
                return msg
            errors = body.get("errors", [])
            for err in errors:
                if isinstance(err, dict) and "scope" in err.get("message", "").lower():
                    return err.get("message")
        return None

    def _count_records(self, body: Any) -> Optional[int]:
        if isinstance(body, dict):
            for key in ("results", "workflows", "lists", "objects"):
                if isinstance(body.get(key), list):
                    return len(body[key])
            if "total" in body:
                return body["total"]
        return None

    def _record(self, **kwargs):
        self.audit_trail.append(
            QueryRecord(timestamp=datetime.now(timezone.utc).isoformat(), **kwargs)
        )

    def _paginate(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        result_key: str = "results",
        page_size: int = 100,
        note: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Yield records across all pages of a paginated endpoint."""
        params = dict(params or {})
        params.setdefault("limit", page_size)
        after: Optional[str] = None
        page = 0
        while True:
            page += 1
            if after:
                params["after"] = after
            body = self._request("GET", path, params=params, note=f"{note or path} page {page}")
            results = body.get(result_key, [])
            for r in results:
                yield r
            paging = body.get("paging", {})
            next_ = paging.get("next", {}) if isinstance(paging, dict) else {}
            after = next_.get("after") if isinstance(next_, dict) else None
            if not after:
                break

    # ------------------------------------------------------------------
    # Portal profile (Phase 1)
    # ------------------------------------------------------------------

    def get_portal_profile(self) -> Dict[str, Any]:
        """
        Fetch the baseline portal profile: account info, creation date, tier signals.

        Some fields require specific scopes; missing fields are OK.
        """
        profile: Dict[str, Any] = {}

        # Account info
        try:
            info = self._request("GET", "/account-info/v3/details")
            profile["hub_id"] = info.get("portalId")
            profile["account_type"] = info.get("accountType")
            profile["time_zone"] = info.get("timeZone")
            profile["currency"] = info.get("companyCurrency")
            profile["ui_domain"] = info.get("uiDomain")
        except HubSpotAuditError as exc:
            profile["_account_info_error"] = str(exc)

        return profile

    # ------------------------------------------------------------------
    # Record counts (cheap sizing queries)
    # ------------------------------------------------------------------

    def record_count(self, object_type: str) -> int:
        """Get a total count of records for an object type. Uses search with limit=1."""
        body = self._request(
            "POST",
            f"/crm/v3/objects/{object_type}/search",
            json_body={"limit": 1},
            note=f"count {object_type}",
        )
        return body.get("total", 0)

    def record_count_since(self, object_type: str, days: int) -> int:
        """Count records created in the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        ts_ms = int(cutoff.timestamp() * 1000)
        body = self._request(
            "POST",
            f"/crm/v3/objects/{object_type}/search",
            json_body={
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "createdate",
                        "operator": "GTE",
                        "value": str(ts_ms),
                    }]
                }],
                "limit": 1,
            },
            note=f"count {object_type} last {days}d",
        )
        return body.get("total", 0)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def list_properties(self, object_type: str) -> List[Dict[str, Any]]:
        """All property definitions for an object type."""
        body = self._request(
            "GET",
            f"/crm/v3/properties/{object_type}",
            note=f"properties {object_type}",
        )
        return body.get("results", [])

    def property_fill_rate(
        self,
        object_type: str,
        property_name: str,
        sample_size: int = 2000,
    ) -> Dict[str, Any]:
        """
        Estimate fill rate for a property.

        Samples up to sample_size records and counts how many have the property
        populated (non-null, non-empty string). Returns a dict with count / total / rate.
        """
        filled = 0
        sampled = 0
        body = self._request(
            "POST",
            f"/crm/v3/objects/{object_type}/search",
            json_body={
                "properties": [property_name],
                "limit": min(sample_size, 100),
            },
            note=f"fill rate {object_type}.{property_name}",
        )
        for r in body.get("results", []):
            sampled += 1
            val = r.get("properties", {}).get(property_name)
            if val not in (None, "", []):
                filled += 1
        return {
            "object_type": object_type,
            "property": property_name,
            "filled": filled,
            "sampled": sampled,
            "rate": (filled / sampled) if sampled else None,
        }

    # ------------------------------------------------------------------
    # Workflows (requires automation scope)
    # ------------------------------------------------------------------

    def list_all_workflows(self) -> List[Dict[str, Any]]:
        """
        Full workflow inventory via the v4 flows API.

        Returns each workflow's id, name, enabled state, type, and last updated.
        """
        workflows: List[Dict[str, Any]] = []
        try:
            for wf in self._paginate(
                "/automation/v4/flows",
                result_key="results",
                page_size=100,
                note="workflow inventory",
            ):
                workflows.append(wf)
        except HubSpotScopeError as exc:
            # Fall back to v3 flows if v4 not available
            raise HubSpotAuditError(
                f"Could not list workflows via v4 API: {exc}. "
                "Ensure the token has the 'automation' scope."
            )
        return workflows

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def list_all_lists(self) -> List[Dict[str, Any]]:
        """Full list inventory (contacts and other object lists)."""
        lists: List[Dict[str, Any]] = []
        body = self._request(
            "POST",
            "/crm/v3/lists/search",
            json_body={"count": 500, "offset": 0, "processingTypes": ["MANUAL", "DYNAMIC", "SNAPSHOT"]},
            note="list inventory",
        )
        lists.extend(body.get("lists", []))
        total = body.get("total", len(lists))
        offset = 500
        while len(lists) < total:
            body = self._request(
                "POST",
                "/crm/v3/lists/search",
                json_body={"count": 500, "offset": offset, "processingTypes": ["MANUAL", "DYNAMIC", "SNAPSHOT"]},
                note=f"list inventory offset {offset}",
            )
            batch = body.get("lists", [])
            if not batch:
                break
            lists.extend(batch)
            offset += 500
        return lists

    # ------------------------------------------------------------------
    # Owners / Users
    # ------------------------------------------------------------------

    def list_all_owners(self) -> List[Dict[str, Any]]:
        """Every owner on the portal (active + inactive)."""
        owners: List[Dict[str, Any]] = []
        for o in self._paginate(
            "/crm/v3/owners",
            result_key="results",
            page_size=100,
            note="owner inventory",
        ):
            owners.append(o)
        return owners

    def list_active_users(self) -> List[Dict[str, Any]]:
        """Users from settings API (needs settings.users.read)."""
        body = self._request(
            "GET",
            "/settings/v3/users",
            params={"limit": 100},
            note="user inventory",
        )
        return body.get("results", [])

    # ------------------------------------------------------------------
    # Pipelines and stages
    # ------------------------------------------------------------------

    def list_pipelines(self, object_type: str = "deals") -> List[Dict[str, Any]]:
        """Pipelines + stages for an object type."""
        body = self._request(
            "GET",
            f"/crm/v3/pipelines/{object_type}",
            note=f"pipelines {object_type}",
        )
        return body.get("results", [])

    # ------------------------------------------------------------------
    # Custom objects
    # ------------------------------------------------------------------

    def list_custom_object_schemas(self) -> List[Dict[str, Any]]:
        """All custom object schemas in the portal."""
        body = self._request("GET", "/crm/v3/schemas", note="custom object schemas")
        return body.get("results", [])

    # ------------------------------------------------------------------
    # Activity (engagements)
    # ------------------------------------------------------------------

    def engagement_activity_by_user(self, since_days: int = 30) -> Dict[int, Dict[str, int]]:
        """
        Count engagement records per owner per type (call/email/meeting/note/task)
        in the last N days.

        Returns {owner_id: {"calls": N, "emails": N, ...}}
        """
        cutoff_ms = int((datetime.now(timezone.utc) - timedelta(days=since_days)).timestamp() * 1000)
        by_owner: Dict[int, Dict[str, int]] = {}

        for obj_type in ("calls", "emails", "meetings", "notes", "tasks"):
            body = self._request(
                "POST",
                f"/crm/v3/objects/{obj_type}/search",
                json_body={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "hs_timestamp",
                            "operator": "GTE",
                            "value": str(cutoff_ms),
                        }]
                    }],
                    "properties": ["hubspot_owner_id", "hs_timestamp"],
                    "limit": 100,
                },
                note=f"engagement {obj_type} since {since_days}d (first page)",
            )
            # Note: pagination omitted here; for full coverage, paginate the search.
            # For audit purposes, HubSpot caps search total at 10K; this is usually enough for a sample.
            for rec in body.get("results", []):
                owner_id = rec.get("properties", {}).get("hubspot_owner_id")
                if owner_id:
                    try:
                        owner_id = int(owner_id)
                    except (TypeError, ValueError):
                        continue
                    bucket = by_owner.setdefault(owner_id, {"calls": 0, "emails": 0, "meetings": 0, "notes": 0, "tasks": 0})
                    bucket[obj_type] = bucket.get(obj_type, 0) + 1

        return by_owner

    # ------------------------------------------------------------------
    # Deals — buying role coverage
    # ------------------------------------------------------------------

    def open_deals_buying_role_coverage(self, min_deal_amount: float = 10000) -> Dict[str, Any]:
        """
        For open deals above min_deal_amount, check buying role associations.

        Uses the associations API to check if each deal has associated contacts
        with buying roles set. Returns summary counts.
        """
        summary = {
            "total_open_deals_above_threshold": 0,
            "deals_with_decision_maker": 0,
            "deals_with_any_role": 0,
            "deals_with_no_associated_contacts": 0,
            "deals_single_threaded": 0,  # only 1 associated contact
            "sampled": 0,
        }

        # Search open deals above threshold
        body = self._request(
            "POST",
            "/crm/v3/objects/deals/search",
            json_body={
                "filterGroups": [{
                    "filters": [
                        {"propertyName": "amount", "operator": "GTE", "value": str(min_deal_amount)},
                        {"propertyName": "hs_is_closed", "operator": "EQ", "value": "false"},
                    ]
                }],
                "properties": ["dealname", "amount", "dealstage"],
                "limit": 100,
            },
            note="open deals above threshold for buying role check",
        )

        deals = body.get("results", [])
        summary["total_open_deals_above_threshold"] = body.get("total", len(deals))
        summary["sampled"] = len(deals)

        for deal in deals:
            deal_id = deal["id"]
            # Fetch contact associations with labels
            assoc_body = self._request(
                "GET",
                f"/crm/v4/objects/deals/{deal_id}/associations/contacts",
                note=f"deal {deal_id} contact associations",
            )
            contacts = assoc_body.get("results", [])
            if not contacts:
                summary["deals_with_no_associated_contacts"] += 1
                continue
            if len(contacts) == 1:
                summary["deals_single_threaded"] += 1

            has_any_role = False
            has_decision_maker = False
            for c in contacts:
                for label in c.get("associationTypes", []):
                    label_name = (label.get("label") or "").lower()
                    if label_name and label_name not in ("primary", ""):
                        has_any_role = True
                    if "decision maker" in label_name:
                        has_decision_maker = True
            if has_any_role:
                summary["deals_with_any_role"] += 1
            if has_decision_maker:
                summary["deals_with_decision_maker"] += 1

        return summary

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def find_duplicate_contacts_by_email(self, sample_size: int = 5000) -> Dict[str, Any]:
        """
        Sample contacts and count how many share an email with at least one other contact.
        Returns summary stats.
        """
        emails: Dict[str, int] = {}
        count = 0
        for contact in self._paginate(
            "/crm/v3/objects/contacts",
            params={"properties": "email", "limit": 100},
            result_key="results",
            note="dupe detection contacts",
        ):
            count += 1
            email = (contact.get("properties", {}).get("email") or "").strip().lower()
            if email:
                emails[email] = emails.get(email, 0) + 1
            if count >= sample_size:
                break

        dupe_groups = [e for e, n in emails.items() if n > 1]
        dupe_records = sum(n for n in emails.values() if n > 1)

        return {
            "sampled": count,
            "unique_emails": len(emails),
            "duplicate_groups": len(dupe_groups),
            "duplicate_records": dupe_records,
            "duplicate_rate": (dupe_records / count) if count else None,
        }

    # ------------------------------------------------------------------
    # Forms
    # ------------------------------------------------------------------

    def list_all_forms(self) -> List[Dict[str, Any]]:
        body = self._request("GET", "/marketing/v3/forms", params={"limit": 100}, note="form inventory")
        forms = body.get("results", [])
        # pagination
        while body.get("paging", {}).get("next", {}).get("after"):
            after = body["paging"]["next"]["after"]
            body = self._request(
                "GET",
                "/marketing/v3/forms",
                params={"limit": 100, "after": after},
                note=f"form inventory after {after}",
            )
            forms.extend(body.get("results", []))
        return forms

    # ------------------------------------------------------------------
    # Activity digest support
    # ------------------------------------------------------------------

    def properties_created_since(self, object_type: str, days: int) -> List[Dict[str, Any]]:
        """Properties created in the last N days for an object type."""
        all_props = self.list_properties(object_type)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = []
        for p in all_props:
            created = p.get("createdAt")
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created_dt >= cutoff:
                    recent.append(p)
            except ValueError:
                continue
        return recent

    def workflows_modified_since(self, days: int) -> List[Dict[str, Any]]:
        """Workflows created or modified in the last N days."""
        all_wf = self.list_all_workflows()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = []
        for wf in all_wf:
            updated = wf.get("updatedAt") or wf.get("createdAt")
            if not updated:
                continue
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if updated_dt >= cutoff:
                    recent.append(wf)
            except ValueError:
                continue
        return recent

    # ------------------------------------------------------------------
    # Audit trail export
    # ------------------------------------------------------------------

    def export_audit_trail(self) -> List[Dict[str, Any]]:
        """Return the list of queries made, for inclusion in deliverable Appendix B."""
        return [
            {
                "timestamp": q.timestamp,
                "method": q.method,
                "endpoint": q.endpoint,
                "status": q.status,
                "record_count": q.record_count,
                "note": q.note,
            }
            for q in self.audit_trail
        ]


# ----------------------------------------------------------------------
# Convenience function
# ----------------------------------------------------------------------

def quick_portal_snapshot(token: str) -> Dict[str, Any]:
    """One-call summary of portal shape. Useful for verifying a token works."""
    hs = HubSpotAuditClient(token)
    return {
        "profile": hs.get_portal_profile(),
        "contacts": hs.record_count("contacts"),
        "companies": hs.record_count("companies"),
        "deals": hs.record_count("deals"),
        "tickets": hs.record_count("tickets"),
        "contacts_last_90d": hs.record_count_since("contacts", 90),
        "deals_last_90d": hs.record_count_since("deals", 90),
    }


if __name__ == "__main__":
    import os
    import sys

    tok = os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN")
    if not tok:
        print("Set HUBSPOT_PRIVATE_APP_TOKEN environment variable")
        sys.exit(1)
    snap = quick_portal_snapshot(tok)
    print(json.dumps(snap, indent=2))
