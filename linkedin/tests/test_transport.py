"""Tests for the v2-preferred / v1-fallback transport.

This module decides, per call, which API version answers -- so what is pinned
here is the ROUTING, not the HTTP. Three things must hold or the routine gets
quietly worse instead of failing:

  1. `profile()` never reaches v2. v2 returns HTTP 200 with no work_experience,
     which reads as "no current role" and writes 'No Longer with Company'
     across the CRM.
  2. A v2 failure degrades to v1 AND records why, so a version problem shows
     up in the run report instead of hiding behind a working run.
  3. The v1-shaped dicts the shim hands back still satisfy `posts.py`, which
     was written against v1 and is not changing.
"""

import json

import pytest

from qbs_linkedin.posts import commented_post_ids, evaluate_post, post_join_key
from qbs_linkedin.transport import (
    V2_ACCOUNT_ID,
    Route,
    UnipileClient,
    decode_v2_post_id,
    v2_comment_to_v1,
    v2_post_to_v1,
)
from qbs_linkedin.unipile import UnipileError

# The real composite id from Shawn's feed, 2026-08-30. Both urns, one field.
REAL_V2_POST_ID = (
    "WyJhY3Rpdml0eTo3NDk2MjgwMjc2OTQ0MjY5MzEzIiwidWdjUG9zdDo3NDk2MjgwMjc2MTA1NDQxMjgwIl0="
)
ACTIVITY_NUM = "7496280276944269313"
UGC_NUM = "7496280276105441280"


class FakeV1:
    """Stands in for the v1 client. Records what was asked of it."""

    def __init__(self, **returns):
        self.calls = []
        self.returns = returns
        self.account_id = "7lBoyXuETqKdiJYLj5HBGA"
        #: The id v1 reports back, separately settable so a test can simulate
        #: the account being absent from the key's account list.
        self.reported_id = self.account_id

    def _record(self, name, *a):
        self.calls.append((name, a))
        return self.returns.get(name)

    def profile(self, identifier, sections="experience"):
        return self._record("profile", identifier) or {"work_experience": []}

    def posts(self, provider_id, limit=10):
        return self._record("posts", provider_id) or {"items": [{"social_id": "v1"}]}

    def self_comments(self, provider_id, limit=100):
        return self._record("self_comments", provider_id) or [{"post_id": "v1"}]

    def accounts(self):
        self._record("accounts")
        return {"items": [{"id": self.reported_id,
                           "sources": [{"id": "LINKEDIN_MESSAGING", "status": "OK"}]}]}


@pytest.fixture(autouse=True)
def no_ambient_v2_key(monkeypatch):
    """Isolate every test in this module from the real environment.

    `UnipileClient` falls back to the env when no key is passed, so without
    this a machine that has UNIPILE_V2_KEY set turns "no key configured" tests
    into live HTTP calls against Unipile — which is how a unit suite starts
    depending on the network and on someone's credentials.
    """
    from qbs_linkedin.transport import V2_KEY_ENV_NAMES
    for name in V2_KEY_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def client(fake=None, v2_key="v2-key", **kw):
    c = UnipileClient(v2_key=v2_key, **kw)
    c._v1 = fake or FakeV1()
    return c


class TestDecodeV2PostId:
    def test_the_real_composite_yields_both_urns(self):
        assert decode_v2_post_id(REAL_V2_POST_ID) == {
            "activity": ACTIVITY_NUM,
            "ugcPost": UGC_NUM,
        }

    def test_missing_base64_padding_is_tolerated(self):
        # v2 has been observed returning the id without trailing '='.
        assert decode_v2_post_id(REAL_V2_POST_ID.rstrip("=")) == {
            "activity": ACTIVITY_NUM,
            "ugcPost": UGC_NUM,
        }

    @pytest.mark.parametrize("bad", [None, "", "not-base64!!", "eyJhIjoxfQ=="])
    def test_anything_unparseable_is_empty_not_an_exception(self, bad):
        # A post we cannot decode must be skippable, not fatal to the run.
        assert decode_v2_post_id(bad) == {}


class TestV2PostReshaping:
    @pytest.fixture
    def shaped(self):
        return v2_post_to_v1({
            "id": REAL_V2_POST_ID,
            "created_at": "2026-08-29T14:02:00Z",
            "comments_counter": 4,
            "reactions_counter": 11,
            "text": "hello",
        })

    def test_social_id_is_rebuilt_in_v1_form(self, shaped):
        assert shaped["social_id"] == f"urn:li:activity:{ACTIVITY_NUM}"

    def test_timestamp_moves_to_the_field_freshness_reads(self, shaped):
        # posts.parse_post_time reads parsed_datetime and NEVER the relative
        # `date` string; created_at has to land there or every post is stale.
        assert shaped["parsed_datetime"] == "2026-08-29T14:02:00Z"

    def test_counters_lose_their_v2_plural(self, shaped):
        assert shaped["comment_counter"] == 4
        assert shaped["reaction_counter"] == 11

    def test_both_urns_are_carried_for_dedupe(self, shaped):
        assert sorted(shaped["_all_urn_ids"]) == sorted([ACTIVITY_NUM, UGC_NUM])

    def test_the_original_fields_survive(self, shaped):
        assert shaped["text"] == "hello"

    def test_a_post_with_only_a_ugcpost_urn_still_gets_a_social_id(self):
        import base64
        pid = base64.b64encode(json.dumps([f"ugcPost:{UGC_NUM}"]).encode()).decode()
        assert v2_post_to_v1({"id": pid})["social_id"] == f"urn:li:ugcPost:{UGC_NUM}"

    def test_an_undecodable_id_yields_no_social_id_rather_than_a_wrong_one(self):
        assert v2_post_to_v1({"id": "garbage"})["social_id"] is None


class TestV2CommentReshaping:
    def test_created_at_becomes_date(self):
        c = v2_comment_to_v1({"created_at": "2026-08-29T14:02:00Z"})
        assert c["date"] == "2026-08-29T14:02:00Z"

    def test_post_id_is_derived_from_the_composite(self):
        c = v2_comment_to_v1({"post": REAL_V2_POST_ID})
        assert c["post_id"] in (ACTIVITY_NUM, UGC_NUM)

    def test_an_explicit_post_id_is_not_overwritten(self):
        c = v2_comment_to_v1({"post_id": "123", "post": REAL_V2_POST_ID})
        assert c["post_id"] == "123"


class TestTheShimSatisfiesPostsPy:
    """The shim's whole justification: v1-era code keeps working unchanged."""

    def test_reshaped_posts_flow_through_commented_post_ids(self):
        ids = commented_post_ids([v2_comment_to_v1({"post": REAL_V2_POST_ID})])
        assert ids and ids <= {ACTIVITY_NUM, UGC_NUM}

    def test_join_key_matches_the_activity_tail(self):
        shaped = v2_post_to_v1({"id": REAL_V2_POST_ID})
        assert post_join_key(shaped["social_id"]) == ACTIVITY_NUM

    def test_dedupe_matches_on_the_ugcpost_urn_too(self):
        # THE TRAP. v1 gave one urn; v2 gives two, and Shawn's comment may
        # carry either tail. Matching only the preferred urn re-comments on a
        # post he already answered — under his name, publicly.
        shaped = v2_post_to_v1({
            "id": REAL_V2_POST_ID,
            "created_at": "2026-08-30T12:00:00Z",
        })
        decision = evaluate_post(shaped, already_commented={UGC_NUM},
                                 freshness_hours=48,
                                 now=__import__("datetime").datetime(
                                     2026, 8, 30, 13, 0,
                                     tzinfo=__import__("datetime").timezone.utc))
        assert decision.eligible is False
        assert decision.reason == "already commented"


class TestProfileIsPinnedToV1:
    def test_profile_never_routes_to_v2_even_with_a_key(self):
        # Measured 2026-08-30: v2 returns HTTP 200 and no work_experience
        # under six parameter variants. A "successful" v2 profile is the
        # exact shape that writes 'No Longer with Company' across the CRM.
        fake = FakeV1(profile={"work_experience": [{"company": "QBS"}]})
        c = client(fake)
        c._v2_get = lambda *a, **k: pytest.fail("profile must not call v2")
        result = c.profile("ACoAAA")
        assert result["work_experience"]
        assert c.route.version == "v1"
        assert "work_experience" in c.route.reason
        assert fake.calls == [("profile", ("ACoAAA",))]


class TestRoutingAndFallback:
    def test_v2_answers_when_it_works(self):
        c = client()
        c._v2_get = lambda path, params=None: {
            "data": [{"id": REAL_V2_POST_ID, "created_at": "2026-08-30T00:00:00Z"}]
        }
        posts = c.posts("ACoAAA")
        assert c.route == Route("v2", "primary")
        assert posts[0]["social_id"] == f"urn:li:activity:{ACTIVITY_NUM}"

    def test_a_v2_failure_falls_back_and_says_why(self):
        fake = FakeV1()
        c = client(fake)

        def boom(path, params=None):
            raise UnipileError("v2 exploded")

        c._v2_get = boom
        assert c.posts("ACoAAA") == [{"social_id": "v1"}]
        assert c.route.version == "v1"
        # Degrading silently is how a version problem stays invisible for
        # twelve weeks. The reason has to name the call and the error.
        assert "posts" in c.route.reason
        assert "v2 exploded" in c.route.reason
        assert fake.calls == [("posts", ("ACoAAA",))]

    def test_no_v2_key_is_recorded_as_a_configuration_fact(self):
        c = client(v2_key="")
        assert c.posts("ACoAAA") == [{"social_id": "v1"}]
        assert c.route == Route("v1", "no v2 key configured")

    def test_a_caller_can_pin_the_whole_client_to_v1(self):
        c = client(prefer="v1")
        c._v2_get = lambda *a, **k: pytest.fail("prefer=v1 must not call v2")
        c.posts("ACoAAA")
        assert c.route == Route("v1", "v1 preferred by caller")

    def test_self_comments_pages_v2_to_the_end(self):
        # A partial dedupe set looks authoritative while causing double
        # comments, so paging must not stop at page one.
        pages = [
            {"data": [{"post": REAL_V2_POST_ID}], "cursor": "c1"},
            {"data": [{"post_id": "999"}], "cursor": None},
        ]
        c = client()
        c._v2_get = lambda path, params=None: pages.pop(0)
        assert len(c.self_comments("ACoAAA")) == 2
        assert pages == []

    def test_the_v2_url_puts_the_account_in_the_path(self):
        # v2 rejects account_id as a query param: must match ^acc_(.*)$
        seen = {}
        c = client()

        def capture(path, params=None):
            seen["path"] = path
            return {"data": []}

        c._v2_get = capture
        c.posts("ACoAAA")
        assert seen["path"] == "/users/ACoAAA/posts"
        assert c.v2_account == V2_ACCOUNT_ID

    def test_a_v2_call_without_a_key_raises_rather_than_sending_it(self):
        c = client(v2_key="")
        with pytest.raises(UnipileError, match="no v2 key"):
            c._v2_get("/accounts")


class TestHealthPrefersV2:
    def test_v2_reports_per_product_status(self, monkeypatch):
        # This is where v2 is strictly better: v1 says OK while Sales
        # Navigator is dead, which is exactly how that went undiagnosed.
        body = json.dumps({
            "status": "OK",
            "is_locked": False,
            "metadata": {"products_connection_status": {
                "classic": "running", "sales_navigator": "running"}},
        }).encode()

        class Resp:
            def read(self): return body
            def __enter__(self): return self
            def __exit__(self, *a): return False

        monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Resp())
        c = client()
        h = c.health()
        assert c.route.version == "v2"
        assert h["source"] == "v2/products_connection_status"
        assert h["products"]["sales_navigator"] == "running"

    def test_the_v1_answer_declares_its_own_blind_spot(self, monkeypatch):
        def boom(*a, **k):
            raise OSError("v2 down")

        monkeypatch.setattr("urllib.request.urlopen", boom)
        c = client()
        h = c.health()
        assert c.route.version == "v1"
        # A caller must not read a v1 answer as if the stronger check ran.
        assert "MESSAGING only" in h["source"]
        assert "Sales Navigator" in h["source"]
        assert h["products"] == {"messaging": "OK"}

    def test_an_account_missing_from_both_versions_raises(self, monkeypatch):
        monkeypatch.setattr("urllib.request.urlopen",
                            lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
        fake = FakeV1()
        fake.reported_id = "someone-else"
        c = client(fake)
        with pytest.raises(UnipileError, match="not found on either version"):
            c.health()


class TestTheKeyIsReadUnderEveryNameItIsStoredAs:
    """The cloud environment holds it as UNIPILE_V2_KEY; earlier docs here
    asked for UNIPILE_V2_API_KEY. That mismatch does not raise — the client
    reports "no v2 key configured" and quietly degrades every call to v1, so
    the migration looks complete while nothing routes to v2."""

    def test_the_name_the_environment_actually_uses(self, monkeypatch):
        from qbs_linkedin.transport import v2_key_from_env
        monkeypatch.setenv("UNIPILE_V2_KEY", "from-v2-key")
        assert v2_key_from_env() == "from-v2-key"

    def test_the_name_the_docs_asked_for(self, monkeypatch):
        from qbs_linkedin.transport import v2_key_from_env
        monkeypatch.setenv("UNIPILE_V2_API_KEY", "from-api-key")
        assert v2_key_from_env() == "from-api-key"

    def test_neither_set_is_empty_not_an_exception(self):
        from qbs_linkedin.transport import v2_key_from_env
        assert v2_key_from_env() == ""

    def test_a_client_with_no_key_anywhere_routes_to_v1(self):
        c = client(v2_key="")
        assert c.posts("ACoAAA") == [{"social_id": "v1"}]
        assert c.route == Route("v1", "no v2 key configured")
