import base64
from unittest.mock import patch

import pytest

from fastmcp_creds import BasicAuthCredentialsProvider, is_unresolved_placeholder_value
from fastmcp_creds.basic_auth import BasicAuthError


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


class TestIsUnresolvedPlaceholderValue:
    def test_bare_placeholder(self):
        assert is_unresolved_placeholder_value("${MY_VAR}") is True

    def test_basic_with_placeholder_token(self):
        assert is_unresolved_placeholder_value("Basic ${MY_CREDS}") is True

    def test_bearer_basic_with_placeholder(self):
        assert is_unresolved_placeholder_value("Bearer Basic ${MY_CREDS}") is True

    def test_real_basic_auth(self):
        assert is_unresolved_placeholder_value(f"Basic {_b64('user:pass')}") is False

    def test_empty_string(self):
        assert is_unresolved_placeholder_value("") is False


class TestBasicAuthCredentialsProvider:
    @patch("fastmcp_creds.basic_auth.get_http_headers")
    def test_standard_authorization_header(self, mock_headers):
        mock_headers.return_value = {"authorization": f"Basic {_b64('alice:secret')}"}
        assert BasicAuthCredentialsProvider().get_credentials() == ("alice", "secret")

    @patch("fastmcp_creds.basic_auth.get_http_headers")
    def test_custom_header_takes_priority(self, mock_headers):
        mock_headers.return_value = {
            "x-custom-auth": f"Basic {_b64('from-custom:pass1')}",
            "authorization": f"Basic {_b64('from-standard:pass2')}",
        }
        assert BasicAuthCredentialsProvider("X-Custom-Auth").get_credentials() == (
            "from-custom",
            "pass1",
        )

    @patch("fastmcp_creds.basic_auth.get_http_headers")
    def test_falls_back_to_standard_header(self, mock_headers):
        mock_headers.return_value = {"authorization": f"Basic {_b64('alice:secret')}"}
        assert BasicAuthCredentialsProvider("X-Missing").get_credentials() == (
            "alice",
            "secret",
        )

    @patch("fastmcp_creds.basic_auth.get_http_headers")
    def test_bearer_basic_variant_accepted(self, mock_headers):
        mock_headers.return_value = {
            "authorization": f"Bearer Basic {_b64('alice:secret')}"
        }
        assert BasicAuthCredentialsProvider().get_credentials() == ("alice", "secret")

    @patch("fastmcp_creds.basic_auth.get_http_headers")
    def test_unresolved_placeholder_returns_none(self, mock_headers):
        mock_headers.return_value = {"authorization": "Basic ${MY_CREDS}"}
        assert BasicAuthCredentialsProvider().get_credentials() == (None, None)

    @patch("fastmcp_creds.basic_auth.get_http_headers")
    def test_no_headers_returns_none(self, mock_headers):
        mock_headers.return_value = {}
        assert BasicAuthCredentialsProvider().get_credentials() == (None, None)

    def test_parse_missing_colon_raises(self):
        provider = BasicAuthCredentialsProvider()
        with pytest.raises(BasicAuthError, match="missing colon"):
            provider._parse_basic_auth_header(
                "Authorization", f"Basic {_b64('nocolon')}"
            )

    def test_parse_empty_username_raises(self):
        provider = BasicAuthCredentialsProvider()
        with pytest.raises(BasicAuthError, match="empty username"):
            provider._parse_basic_auth_header(
                "Authorization", f"Basic {_b64(':password')}"
            )
