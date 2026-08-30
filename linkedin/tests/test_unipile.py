"""Tests for the Unipile transport.

The URL construction is the whole point of this module, so that is what is
pinned here: the tenant port must leave the host and travel as a query
parameter, or the request goes to a port this environment cannot reach.
"""

import pytest

from qbs_linkedin.config import SHAWN_ACCOUNT_ID
from qbs_linkedin.unipile import (
    DEFAULT_DSN,
    Unipile,
    UnipileError,
    base_url,
    split_dsn,
)


class TestDsnParsing:
    @pytest.mark.parametrize("raw", [
        "api30.unipile.com:16072",
        "https://api30.unipile.com:16072",
        "https://api30.unipile.com:16072/",
        "http://api30.unipile.com:16072",
    ])
    def test_every_written_form_parses_the_same(self, raw):
        assert split_dsn(raw) == ("api30.unipile.com", "16072")

    def test_a_dsn_without_a_port(self):
        assert split_dsn("api30.unipile.com") == ("api30.unipile.com", None)

    def test_default_matches_the_dashboard(self):
        # What the Unipile dashboard prints under "Your DSN".
        assert DEFAULT_DSN == "api30.unipile.com:16072"


class TestBaseUrlNeverCarriesThePort:
    def test_host_only_on_443(self):
        # The fix in one assertion. A base URL carrying :16072 is unreachable
        # from this environment — the request never leaves the container.
        url = base_url("api30.unipile.com:16072")
        assert url == "https://api30.unipile.com/api/v1"
        assert ":16072" not in url


class TestRequestUrls:
    @pytest.fixture
    def client(self):
        return Unipile(api_key="test-key-1234567890.abcdefghij",
                       dsn="api30.unipile.com:16072")

    def test_port_travels_as_a_query_parameter(self, client):
        url = client._url("/accounts")
        assert url.startswith("https://api30.unipile.com/api/v1/accounts?")
        assert "port=16072" in url
        assert "api30.unipile.com:16072" not in url

    def test_account_id_defaults_to_shawn(self, client):
        assert f"account_id={SHAWN_ACCOUNT_ID}" in client._url("/accounts")

    def test_caller_params_survive(self, client):
        url = client._url("/users/abc", {"linkedin_sections": "experience"})
        assert "linkedin_sections=experience" in url
        assert "port=16072" in url

    def test_no_port_param_when_the_dsn_has_none(self):
        c = Unipile(api_key="test-key-1234567890.abcdefghij",
                    dsn="api30.unipile.com")
        assert "port=" not in c._url("/accounts")

    def test_explicit_account_id_is_honoured(self):
        c = Unipile(api_key="test-key-1234567890.abcdefghij",
                    account_id="7lBoyXuETqKdiJYLj5HBGA")
        assert "account_id=7lBoyXuETqKdiJYLj5HBGA" in c._url("/accounts")


class TestMissingKey:
    def test_absent_key_is_an_instrument_failure_not_a_finding(self, monkeypatch):
        monkeypatch.delenv("UNIPILE_API_KEY", raising=False)
        with pytest.raises(UnipileError, match="NOT the same"):
            Unipile()


class TestWriteGuard:
    def test_a_colleagues_account_cannot_post_a_comment(self, monkeypatch):
        # The key spans seven accounts and five people. A comment from the
        # wrong one publishes under a colleague's name.
        c = Unipile(api_key="test-key-1234567890.abcdefghij",
                    account_id="9eK50zZlT2qVr0oCo0NJVg")
        with pytest.raises(PermissionError, match="Refusing to act"):
            c.post_comment("urn:li:activity:123", "hello")
