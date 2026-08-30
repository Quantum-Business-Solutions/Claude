"""Tests for post selection and comment dedupe.

Fixtures use the real identifier shapes from the live API, because every bug
these guard comes from those shapes contradicting the obvious implementation.
"""

from datetime import datetime, timedelta, timezone

import pytest

from qbs_linkedin.posts import (
    commented_post_ids,
    evaluate_post,
    parse_post_time,
    post_join_key,
)

NOW = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)


def a_post(**overrides):
    post = {
        "social_id": "urn:li:activity:7487565477435670528",
        "id": "7487565477435670528",
        "parsed_datetime": (NOW - timedelta(hours=2)).isoformat(),
        "is_repost": False,
    }
    post.update(overrides)
    return post


class TestJoinKey:
    @pytest.mark.parametrize("social_id,expected", [
        ("urn:li:activity:7487565477435670528", "7487565477435670528"),
        ("urn:li:ugcPost:7495561989247856640", "7495561989247856640"),
        ("urn:li:groupPost:2037595-7479963401075593216",
         "2037595-7479963401075593216"),
    ])
    def test_takes_the_tail_of_social_id(self, social_id, expected):
        assert post_join_key(social_id) == expected

    def test_the_posts_own_id_is_a_different_number(self):
        # Real pair. Joining on `id` silently returns False for every ugcPost
        # and groupPost — roughly half a feed.
        post = {"social_id": "urn:li:ugcPost:7495561989247856640",
                "id": "7495561990287826944"}
        assert post_join_key(post["social_id"]) != post["id"]

    def test_missing(self):
        assert post_join_key(None) is None


class TestCommentedPostIds:
    def test_builds_the_set_from_shawns_own_comments(self):
        comments = [
            {"post_id": "7495818623802916864"},
            {"post_urn": "urn:li:ugcPost:7496674257868075009"},
        ]
        assert commented_post_ids(comments) == {
            "7495818623802916864", "7496674257868075009"
        }

    def test_a_reply_is_included(self):
        # The whole reason this endpoint replaces per-post reads: Shawn's
        # comment on activity 7495818623802916864 was a REPLY, and the
        # post's own comment list reported "complete" without it.
        reply = {"id": "7498144322144481280",
                 "post_urn": "urn:li:activity:7495818623802916864",
                 "thread_id": "7495910984549683200"}
        assert "7495818623802916864" in commented_post_ids([reply])

    def test_empty_and_malformed(self):
        assert commented_post_ids([]) == set()
        assert commented_post_ids([{"text": "no ids here"}]) == set()


class TestPostTime:
    def test_parses_iso_with_z(self):
        assert parse_post_time("2026-08-25T22:27:54.193Z") is not None

    @pytest.mark.parametrize("raw", ["3d", "1w", "1mo", None, ""])
    def test_relative_strings_are_not_timestamps(self, raw):
        # `date` is a relative string and is useless for a freshness window.
        assert parse_post_time(raw) is None


class TestEvaluatePost:
    def test_fresh_uncommented_post_is_eligible(self):
        d = evaluate_post(a_post(), set(), 24, NOW)
        assert d.eligible

    def test_already_commented_is_excluded(self):
        d = evaluate_post(a_post(), {"7487565477435670528"}, 24, NOW)
        assert not d.eligible and d.reason == "already commented"

    def test_dedupe_matches_on_social_id_not_id(self):
        post = a_post(social_id="urn:li:ugcPost:7495561989247856640",
                      id="7495561990287826944")
        # The set holds what Comment.post_id would carry.
        assert not evaluate_post(post, {"7495561989247856640"}, 24, NOW).eligible
        # Keying on the post's own id would wrongly let it through.
        assert evaluate_post(post, {"7495561990287826944"}, 24, NOW).eligible

    def test_stale_post_is_excluded(self):
        old = a_post(parsed_datetime=(NOW - timedelta(hours=30)).isoformat())
        assert not evaluate_post(old, set(), 24, NOW).eligible

    def test_boundary_is_inclusive_of_the_window(self):
        edge = a_post(parsed_datetime=(NOW - timedelta(hours=24)).isoformat())
        assert evaluate_post(edge, set(), 24, NOW).eligible

    def test_reshare_is_skipped(self):
        # parsed_datetime is the RESHARE time, so a window admits someone
        # resharing months-old content, and the text we would score is the
        # resharer's one-liner rather than the substance.
        assert not evaluate_post(a_post(is_repost=True), set(), 24, NOW).eligible

    def test_group_post_is_skipped(self):
        post = a_post(social_id="urn:li:groupPost:2037595-7479963401075593216")
        d = evaluate_post(post, set(), 24, NOW)
        assert not d.eligible and "group post" in d.reason

    def test_missing_timestamp_is_never_treated_as_fresh(self):
        assert not evaluate_post(a_post(parsed_datetime=None), set(), 24, NOW).eligible

    def test_future_timestamp_is_refused(self):
        # article.published_at carries impossible values — a 2028 date was
        # observed on a same-day post.
        future = a_post(parsed_datetime=(NOW + timedelta(days=400)).isoformat())
        d = evaluate_post(future, set(), 24, NOW)
        assert not d.eligible and "future" in d.reason

    def test_comments_disabled(self):
        post = a_post(permissions={"can_post_comments": False})
        assert not evaluate_post(post, set(), 24, NOW).eligible

    def test_no_social_id(self):
        assert not evaluate_post({"id": "123"}, set(), 24, NOW).eligible

    def test_exclusion_order_puts_dedupe_before_freshness(self):
        # A stale post already commented on should report the commented
        # reason, so reports do not misattribute why nothing was posted.
        stale_and_seen = a_post(
            parsed_datetime=(NOW - timedelta(hours=99)).isoformat())
        d = evaluate_post(stale_and_seen, {"7487565477435670528"}, 24, NOW)
        assert d.reason == "already commented"


class TestDedupeCompleteness:
    """A partial dedupe set is worse than none — it looks authoritative."""

    def test_partial_page_read_is_refused(self):
        from qbs_linkedin.posts import IncompleteDedupeError
        # Shawn's live feed is 26 pages at limit=25. Reading page one covers
        # his newest 25 comments and silently re-comments on everything older.
        with pytest.raises(IncompleteDedupeError, match="1 of 26"):
            commented_post_ids([{"post_id": "1"}], pages_fetched=1, page_count=26)

    def test_full_read_is_accepted(self):
        got = commented_post_ids([{"post_id": "1"}], pages_fetched=26, page_count=26)
        assert got == {"1"}

    def test_unknown_page_count_does_not_block(self):
        assert commented_post_ids([{"post_id": "1"}]) == {"1"}
