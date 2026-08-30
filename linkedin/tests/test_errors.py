"""The Unipile error taxonomy, pinned against the published API spec.

Every slug below is copied from the error enums in Unipile's OpenAPI
document (the `responses` block of `GET /api/v1/users/{identifier}`, which
carries the shared error schemas). The point of the conformance test is that
an unclassified code stops being an operational surprise: when Unipile adds
one, this file fails in CI instead of a routine halting at 6am.

Why the direction of each mapping matters more than the mapping itself:
HALT is the correct DEFAULT for something unrecognised, but it is the wrong
answer for an ordinary per-candidate condition. Before this was reconciled,
31 of the 55 published codes fell through to HALT — including
`comments_disabled`, so a single post with comments turned off would end the
entire engagement run.
"""

import pytest

from qbs_linkedin.errors import (
    Action,
    SPEC_ERROR_SLUGS,
    USAGE_STOP_THRESHOLD,
    classify,
)

#: The published enums, by the HTTP status that carries them.
SPEC: dict[int, list[str]] = {
    401: ["missing_credentials", "multiple_sessions", "invalid_checkpoint_solution",
          "invalid_proxy_credentials", "checkpoint_error", "invalid_credentials",
          "expired_credentials", "insufficient_privileges", "disconnected_account",
          "disconnected_feature", "invalid_credentials_but_valid_account_imap",
          "expired_link", "wrong_account"],
    403: ["account_restricted", "account_mismatch", "insufficient_permissions",
          "session_mismatch", "feature_not_subscribed", "subscription_required",
          "unknown_authentication_context", "action_required",
          "resource_access_restricted"],
    404: ["resource_not_found", "invalid_resource_identifier"],
    422: ["invalid_account", "invalid_recipient", "no_connection_with_recipient",
          "blocked_recipient", "user_unreachable", "unprocessable_entity",
          "payment_error", "action_already_performed", "invalid_message",
          "invalid_post", "not_allowed_inmail", "insufficient_credits",
          "cannot_resend_yet", "cannot_resend_within_24hrs", "limit_exceeded",
          "already_invited_recently", "already_connected", "cannot_invite_attendee",
          "comments_disabled", "insufficient_job_slot"],
    429: ["too_many_requests"],
    500: ["unexpected_error", "provider_error", "authentication_intent_error"],
    501: ["feature_not_implemented"],
    503: ["no_client_session", "no_channel", "no_handler", "network_down",
          "service_unavailable"],
    504: ["request_timeout"],
}

ALL_SLUGS = sorted({s for slugs in SPEC.values() for s in slugs})


def response(slug: str, status: int) -> dict:
    return {"type": f"errors/{slug}", "status": status, "detail": slug}


class TestSpecConformance:
    def test_every_published_code_is_classified(self):
        unclassified = sorted(set(ALL_SLUGS) - SPEC_ERROR_SLUGS)
        assert not unclassified, (
            f"{len(unclassified)} published error codes fall through to HALT: "
            f"{unclassified}"
        )

    def test_we_do_not_classify_codes_the_api_never_sends(self):
        # Two invented slugs used to sit here: 'already_invited' (the real one
        # is already_invited_recently) and 'cant_resend_yet' (a typo for
        # cannot_resend_yet), so the condition it was written to skip halted.
        invented = sorted(SPEC_ERROR_SLUGS - set(ALL_SLUGS))
        assert not invented, f"not in the published enum: {invented}"

    @pytest.mark.parametrize("slug", ALL_SLUGS)
    def test_no_published_code_reaches_the_unknown_fallback(self, slug):
        status = next(c for c, s in SPEC.items() if slug in s)
        assert "unclassified" not in classify(response(slug, status), status).reason


class TestTheDirectionsThatCostMost:
    @pytest.mark.parametrize("slug", [
        "comments_disabled",          # one post with comments off
        "user_unreachable",
        "blocked_recipient",
        "no_connection_with_recipient",
        "not_allowed_inmail",
        "cannot_resend_yet",
        "cannot_resend_within_24hrs",
        "cannot_invite_attendee",
        "invalid_recipient",
    ])
    def test_a_per_candidate_problem_skips_rather_than_ending_the_run(self, slug):
        assert classify(response(slug, 422), 422).action is Action.SKIP

    @pytest.mark.parametrize("slug", [
        "account_restricted", "multiple_sessions", "checkpoint_error",
        "disconnected_account", "invalid_credentials", "wrong_account",
        "account_mismatch",
    ])
    def test_an_account_problem_pages_a_human(self, slug):
        v = classify(response(slug, 401), 401)
        assert v.action is Action.HALT and v.is_fatal

    @pytest.mark.parametrize("slug", [
        "too_many_requests", "limit_exceeded", "insufficient_credits",
    ])
    def test_a_volume_refusal_stops_the_day_without_retrying(self, slug):
        assert classify(response(slug, 429), 429).action is Action.STOP_FOR_DAY

    @pytest.mark.parametrize("slug", [
        "provider_error", "service_unavailable", "network_down", "no_handler",
        "no_client_session", "no_channel", "request_timeout", "unexpected_error",
    ])
    def test_a_transient_fault_retries(self, slug):
        assert classify(response(slug, 503), 503).action is Action.RETRY

    @pytest.mark.parametrize("slug", [
        "already_connected", "already_invited_recently", "action_already_performed",
    ])
    def test_an_action_already_taken_still_writes_the_crm_record(self, slug):
        # Skipping the write burns the prospect again on every future run.
        v = classify(response(slug, 422), 422)
        assert v.action is Action.SKIP and v.log_anyway


class TestTheUnknownDefaultIsStillHalt:
    def test_an_unrecognised_error_halts_rather_than_retrying(self):
        v = classify({"type": "errors/something_brand_new", "status": 418}, 418)
        assert v.action is Action.HALT
        assert "unclassified HTTP 418" in v.reason

    def test_an_error_with_no_type_at_all_halts(self):
        assert classify({"status": 500}, 500).action is Action.HALT


class TestTheQuotaSignalInSuccessBodies:
    def test_usage_at_the_threshold_stops_the_day(self):
        v = classify({"usage": USAGE_STOP_THRESHOLD, "invitation_id": "x"})
        assert v.action is Action.STOP_FOR_DAY and v.log_anyway

    def test_usage_below_the_threshold_proceeds(self):
        assert classify({"usage": 75}).action is Action.PROCEED

    def test_a_plain_success_proceeds(self):
        assert classify({"invitation_id": "x"}).action is Action.PROCEED
