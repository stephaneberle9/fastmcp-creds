import os
from unittest.mock import patch

from fastmcp_creds import EnvironmentCredentialsProvider


class TestEnvironmentCredentialsProvider:
    def test_returns_credentials_from_env_vars(self):
        provider = EnvironmentCredentialsProvider("MY_USER", "MY_PASS")
        with patch.dict(os.environ, {"MY_USER": "alice", "MY_PASS": "secret"}):
            assert provider.get_credentials() == ("alice", "secret")

    def test_returns_none_when_vars_missing(self):
        provider = EnvironmentCredentialsProvider("MY_USER", "MY_PASS")
        with patch.dict(os.environ, {}, clear=True):
            assert provider.get_credentials() == (None, None)

    def test_returns_none_when_only_username_set(self):
        provider = EnvironmentCredentialsProvider("MY_USER", "MY_PASS")
        with patch.dict(os.environ, {"MY_USER": "alice"}, clear=True):
            assert provider.get_credentials() == (None, None)

    def test_returns_none_when_only_password_set(self):
        provider = EnvironmentCredentialsProvider("MY_USER", "MY_PASS")
        with patch.dict(os.environ, {"MY_PASS": "secret"}, clear=True):
            assert provider.get_credentials() == (None, None)

    def test_token_mode_returns_token_for_both_positions(self):
        provider = EnvironmentCredentialsProvider.for_token("MY_TOKEN")
        with patch.dict(os.environ, {"MY_TOKEN": "tok-abc123"}):
            assert provider.get_credentials() == ("tok-abc123", "tok-abc123")

    def test_token_mode_returns_none_when_var_missing(self):
        provider = EnvironmentCredentialsProvider.for_token("MY_TOKEN")
        with patch.dict(os.environ, {}, clear=True):
            assert provider.get_credentials() == (None, None)
