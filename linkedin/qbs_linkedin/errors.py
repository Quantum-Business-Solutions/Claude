"""Unipile response classification.

Deciding whether a failure means *retry*, *skip this one*, *stop for today* or
*stop and page a human* is the difference between a transient hiccup and a
restricted LinkedIn account. Getting it wrong in the lenient direction — say,
retrying through a throttle — is how accounts get flagged.

Two things make this harder than reading a status code:

1. The only authoritative quota signal is ``usage`` in the **success** body of
   an invite response, firing at 50/75/90/95. A send path that inspects status
   codes alone throws it away.
2. The Unipile MCP passthrough returns the response **body only, no headers**,
   so ``Retry-After`` and ``X-RateLimit-*`` are unreadable on the only
   transport that works from a Claude Code container. Budget has to come from
   body fields plus our own counters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    """What the caller should do next."""

    PROCEED = "proceed"          # success, keep going
    SKIP = "skip"                # this candidate only; not a failure
    RETRY = "retry"              # transient; try again later
    STOP_FOR_DAY = "stop_day"    # provider limit; no more sends today
    HALT = "halt"                # session/account problem; page a human


@dataclass(frozen=True)
class Verdict:
    action: Action
    reason: str
    #: True when the candidate should still get its HubSpot record written.
    #: "already invited" is not a failure, and skipping the write there burns
    #: the prospect again on every future run.
    log_anyway: bool = False

    @property
    def is_fatal(self) -> bool:
        return self.action in (Action.STOP_FOR_DAY, Action.HALT)


#: Not failures. The action already happened, or cannot be repeated.
BENIGN = {"already_invited_recently", "already_connected",
          "action_already_performed"}

#: Transient provider-side problems.
RETRYABLE = {"provider_error", "request_timeout", "service_unavailable",
             "network_down", "no_client_session", "no_channel", "no_handler",
             "unexpected_error"}

#: Provider is refusing volume. Stop sending today; do not retry.
LIMIT = {"too_many_requests", "limit_exceeded", "insufficient_credits",
         "insufficient_job_slot"}

#: Session or account problems. A human must intervene; retrying makes it worse.
FATAL = {"account_restricted", "checkpoint_error", "disconnected_account",
         "multiple_sessions", "invalid_credentials", "expired_credentials",
         "insufficient_privileges", "invalid_checkpoint_solution",
         "account_mismatch", "wrong_account", "disconnected_feature",
         "missing_credentials", "invalid_proxy_credentials", "expired_link",
         "invalid_credentials_but_valid_account_imap",
         "insufficient_permissions", "session_mismatch", "feature_not_subscribed",
         "subscription_required", "unknown_authentication_context",
         "action_required", "resource_access_restricted", "invalid_account",
         "feature_not_implemented", "authentication_intent_error"}

#: This candidate cannot be actioned, but the run is fine. Getting these
#: wrong is expensive in the other direction: every one of them used to fall
#: through to HALT, so a single post with comments turned off ended the run.
SKIPPABLE = {"invalid_recipient", "resource_not_found",
             "invalid_resource_identifier", "cannot_resend_yet",
             "cannot_resend_within_24hrs", "no_connection_with_recipient",
             "blocked_recipient", "user_unreachable", "not_allowed_inmail",
             "cannot_invite_attendee", "comments_disabled", "invalid_post",
             "invalid_message", "unprocessable_entity", "payment_error"}

#: Everything above, checked against the full enum in Unipile's OpenAPI spec.
#: `test_errors.py` fails if the spec grows a code we do not classify, so a
#: new failure mode surfaces as a test failure rather than as a halted run.
SPEC_ERROR_SLUGS = frozenset(
    BENIGN | RETRYABLE | LIMIT | FATAL | SKIPPABLE
)

#: Quota percentage at which to stop volunteering for more.
USAGE_STOP_THRESHOLD = 90


def _slug(error_type: str | None) -> str:
    """`errors/too_many_requests` -> `too_many_requests`."""
    return (error_type or "").rsplit("/", 1)[-1].strip().lower()


def classify(response: dict | None, status: int | None = None) -> Verdict:
    """Turn a Unipile response into an action.

    ``status`` may be omitted — the MCP passthrough puts it in the body — and
    an unrecognised error is treated as HALT rather than retried. An unknown
    failure mode on a live LinkedIn account is not something to guess through.
    """
    if response is None:
        return Verdict(Action.RETRY, "empty response")

    code = status if status is not None else response.get("status")
    kind = _slug(response.get("type"))
    detail = response.get("detail") or response.get("title") or kind or "unknown"

    if kind in FATAL:
        return Verdict(Action.HALT, f"{kind}: {detail}")
    if kind in LIMIT:
        return Verdict(Action.STOP_FOR_DAY, f"{kind}: {detail}")
    if kind in BENIGN:
        # Still write the CRM record, or this prospect is re-attempted forever.
        return Verdict(Action.SKIP, f"{kind}: {detail}", log_anyway=True)
    if kind in SKIPPABLE:
        return Verdict(Action.SKIP, f"{kind}: {detail}")
    if kind in RETRYABLE:
        return Verdict(Action.RETRY, f"{kind}: {detail}")

    if isinstance(code, int) and code >= 400:
        # An unclassified error. Stop rather than guess -- see module docstring.
        return Verdict(Action.HALT, f"unclassified HTTP {code}: {detail}")

    # Success. The quota signal lives here, not in the status code.
    usage = response.get("usage")
    if isinstance(usage, (int, float)) and usage >= USAGE_STOP_THRESHOLD:
        return Verdict(
            Action.STOP_FOR_DAY,
            f"provider quota at {usage}% (threshold {USAGE_STOP_THRESHOLD}%)",
            log_anyway=True,
        )
    return Verdict(Action.PROCEED, "ok")


def should_abort_run(errors_so_far: int, max_errors: int = 2) -> bool:
    """More than a couple of real errors means something systemic is wrong."""
    return errors_so_far > max_errors
