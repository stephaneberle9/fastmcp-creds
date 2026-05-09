from unittest.mock import patch

from fastmcp_creds import CustomHeaderCredentialsProvider


class TestCustomHeaderCredentialsProvider:
    @patch("fastmcp_creds.header.get_http_headers")
    def test_reads_from_custom_headers(self, mock_headers):
        mock_headers.return_value = {"x-username": "alice", "x-password": "secret"}
        provider = CustomHeaderCredentialsProvider("X-Username", "X-Password")
        assert provider.get_credentials() == ("alice", "secret")

    @patch("fastmcp_creds.header.get_http_headers")
    def test_case_insensitive_lookup(self, mock_headers):
        mock_headers.return_value = {"X-Username": "alice", "X-Password": "secret"}
        provider = CustomHeaderCredentialsProvider("X-Username", "X-Password")
        assert provider.get_credentials() == ("alice", "secret")

    @patch("fastmcp_creds.header.get_http_headers")
    def test_unresolved_placeholder_ignored(self, mock_headers):
        mock_headers.return_value = {"x-username": "${MY_USER}", "x-password": "secret"}
        provider = CustomHeaderCredentialsProvider("X-Username", "X-Password")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.header.get_http_headers")
    def test_partial_headers_returns_none(self, mock_headers):
        mock_headers.return_value = {"x-username": "alice"}
        provider = CustomHeaderCredentialsProvider("X-Username", "X-Password")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.header.get_http_headers")
    def test_empty_headers_returns_none(self, mock_headers):
        mock_headers.return_value = {}
        provider = CustomHeaderCredentialsProvider("X-Username", "X-Password")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.header.get_http_headers")
    def test_token_mode_returns_token_for_both_positions(self, mock_headers):
        mock_headers.return_value = {"x-token": "tok-abc123"}
        provider = CustomHeaderCredentialsProvider.for_token("X-Token")
        assert provider.get_credentials() == ("tok-abc123", "tok-abc123")

    @patch("fastmcp_creds.header.get_http_headers")
    def test_token_mode_returns_none_when_header_missing(self, mock_headers):
        mock_headers.return_value = {}
        provider = CustomHeaderCredentialsProvider.for_token("X-Token")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.header.get_http_headers")
    def test_token_mode_ignores_unresolved_placeholder(self, mock_headers):
        mock_headers.return_value = {"x-token": "${MY_TOKEN}"}
        provider = CustomHeaderCredentialsProvider.for_token("X-Token")
        assert provider.get_credentials() == (None, None)
