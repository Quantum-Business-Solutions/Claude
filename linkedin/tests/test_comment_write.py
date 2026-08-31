"""The comment write path — the only thing in this program that publishes.

Every test here is about a way a comment could go out wrong: as the wrong
person, twice on one post, truncated, outside hours, over the cap, or recorded
as sent when it was not. The cost of each is public and under Shawn's name, so
the guards are asserted rather than assumed.

The request shape itself is pinned against the published schema for
POST /api/v1/posts/{post_id}/comments, because the first version of this
method — which had never been called — got it wrong twice: it sent a
urlencoded body where multipart is required, and put account_id in the query
where the schema requires it in the body.
"""

import json

import pytest

from qbs_linkedin.config import SHAWN_ACCOUNT_ID
from qbs_linkedin.transport import Route, UnipileClient
from qbs_linkedin.unipile import COMMENT_MAX_CHARS, Unipile, UnipileError, _multipart

ACTIVITY = "urn:li:activity:7496280276944269313"


class TestTheMultipartBody:
    def test_it_is_multipart_not_urlencoded(self):
        body, ctype = _multipart({"account_id": "A", "text": "hi"})
        assert ctype.startswith("multipart/form-data; boundary=")
        assert b'Content-Disposition: form-data; name="account_id"' in body

    def test_the_boundary_matches_the_body(self):
        body, ctype = _multipart({"text": "hi"})
        boundary = ctype.split("boundary=", 1)[1]
        assert body.startswith(f"--{boundary}\r\n".encode())
        assert body.endswith(f"--{boundary}--\r\n".encode())

    def test_account_id_travels_in_the_body(self):
        # The schema lists account_id as a REQUIRED requestBody field. It was
        # previously only in the query string, where the route ignores it.
        body, _ = _multipart({"account_id": SHAWN_ACCOUNT_ID, "text": "hi"})
        assert SHAWN_ACCOUNT_ID.encode() in body

    def test_a_boundary_is_unique_per_call(self):
        assert _multipart({"text": "a"})[1] != _multipart({"text": "a"})[1]


class TestRefusalsBeforeAnyRequest:
    """Each of these must fail without touching the network."""

    @pytest.fixture
    def client(self):
        c = Unipile(api_key="test-key-1234567890.abcdefghij")
        c._sent = []
        return c

    def test_a_colleagues_account_cannot_post(self):
        c = Unipile(api_key="test-key-1234567890.abcdefghij",
                    account_id="9eK50zZlT2qVr0oCo0NJVg")
        with pytest.raises(PermissionError, match="Refusing to act"):
            c.post_comment(ACTIVITY, "hello")

    def test_an_empty_comment_is_refused(self, client):
        with pytest.raises(UnipileError, match="empty comment"):
            client.post_comment(ACTIVITY, "   ")

    def test_a_comment_over_the_provider_limit_is_refused(self, client):
        with pytest.raises(UnipileError, match="over the provider"):
            client.post_comment(ACTIVITY, "x" * (COMMENT_MAX_CHARS + 1))

    def test_a_comment_at_exactly_the_limit_is_not_refused_for_length(self, client, monkeypatch):
        # Boundary: the cap is inclusive, so this must fail later (on the
        # network) rather than on the length check.
        monkeypatch.setattr("urllib.request.urlopen",
                            lambda *a, **k: (_ for _ in ()).throw(OSError("no network")))
        with pytest.raises(Exception) as exc:
            client.post_comment(ACTIVITY, "x" * COMMENT_MAX_CHARS)
        assert "over the provider" not in str(exc.value)

    @pytest.mark.parametrize("bad", ["", None, "7496280276944269313", "activity-123"])
    def test_a_numeric_url_id_is_refused_because_the_route_rejects_it(self, client, bad):
        # The schema is explicit: "The post id visible in url will not work in
        # all case" — use social_id. A numeric id silently 404s per-post.
        with pytest.raises(UnipileError, match="not a social_id"):
            client.post_comment(bad, "hello")


class TestOnlyAVerifiedSendCounts:
    @pytest.fixture
    def client(self):
        return Unipile(api_key="test-key-1234567890.abcdefghij")

    def _respond(self, monkeypatch, payload, status=201):
        class Resp:
            def read(self): return json.dumps(payload).encode()
            @property
            def status(self): return status
            def __enter__(self): return self
            def __exit__(self, *a): return False
        monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Resp())

    def test_the_documented_201_shape_is_a_send(self, client, monkeypatch):
        self._respond(monkeypatch, {"object": "CommentSent", "comment_id": "c1"})
        assert client.post_comment(ACTIVITY, "hello")["comment_id"] == "c1"

    def test_a_200_that_is_not_CommentSent_is_NOT_recorded_as_a_send(self, client, monkeypatch):
        # A phantom ledger entry is worse than a failed post: it consumes cap
        # and claims a comment exists that nobody can find.
        self._respond(monkeypatch, {"object": "SomethingElse"}, status=200)
        with pytest.raises(UnipileError, match="not CommentSent"):
            client.post_comment(ACTIVITY, "hello")

    def test_comments_disabled_skips_rather_than_halting(self, client, monkeypatch):
        self._respond(monkeypatch, {"type": "errors/comments_disabled", "status": 422})
        with pytest.raises(UnipileError, match="comments_disabled"):
            client.post_comment(ACTIVITY, "hello")


class TestWritesAreNeverRoutedToV2OrRetried:
    def test_post_comment_pins_v1_and_says_why(self, monkeypatch):
        monkeypatch.setenv("UNIPILE_V2_KEY", "a-real-looking-v2-key")
        c = UnipileClient()

        class FakeV1:
            account_id = SHAWN_ACCOUNT_ID
            def post_comment(self, social, text): return {"object": "CommentSent"}

        c._v1 = FakeV1()
        c._v2_get = lambda *a, **k: pytest.fail("a write must never touch v2")
        c.post_comment(ACTIVITY, "hello")
        assert c.route == Route("v1", "writes are never routed to v2 or retried")

    def test_the_client_refuses_a_non_shawn_account_too(self, monkeypatch):
        monkeypatch.delenv("UNIPILE_V2_KEY", raising=False)
        c = UnipileClient(v2_key="")

        class FakeV1:
            account_id = "9eK50zZlT2qVr0oCo0NJVg"
            def post_comment(self, social, text):
                pytest.fail("should have been refused before reaching v1")

        c._v1 = FakeV1()
        with pytest.raises(PermissionError):
            c.post_comment(ACTIVITY, "hello")


class TestTheIndependentCount:
    """`decide_allowance` requires it, and it must come from outside HubSpot."""

    def _client(self, comments):
        c = UnipileClient(v2_key="")
        c.self_comments = lambda pid, limit=100: comments
        return c

    def test_it_counts_only_comments_inside_the_day(self):
        # Bounds come from chicago_day_bounds, the same function the caller
        # uses — hardcoding epoch-ms here just tests my arithmetic.
        from datetime import date
        from qbs_linkedin.ledger import chicago_day_bounds
        start, end = chicago_day_bounds(date(2026, 8, 31))
        c = self._client([
            {"date": "2026-08-31T14:00:00Z"},   # inside the Chicago day
            {"date": "2026-08-31T18:00:00Z"},   # inside
            {"date": "2026-08-25T14:00:00Z"},   # older
            {"date": "2026-08-31T04:00:00Z"},   # 23:00 Aug 30 local — OUTSIDE
        ])
        assert c.comments_today("ACo", start, end) == 2

    def test_an_unparseable_timestamp_is_not_counted_as_today(self):
        # Counting it would inflate the independent count and halt a healthy
        # run; ignoring it risks under-counting. Under-counting is caught by
        # the ledger comparison, so ignoring is the safer direction.
        c = self._client([{"date": "3d"}, {"date": None}, {}])
        assert c.comments_today("ACo", 0, 9_999_999_999_999) == 0

    def test_a_paging_failure_raises_rather_than_returning_a_low_count(self):
        def boom(pid, limit=100):
            raise UnipileError("feed paging failed")
        c = UnipileClient(v2_key="")
        c.self_comments = boom
        with pytest.raises(UnipileError):
            c.comments_today("ACo", 0, 1)
