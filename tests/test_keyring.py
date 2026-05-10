from unittest.mock import patch

from fastmcp_creds.keyring import KeyringCredentialsProvider


class TestKeyringCredentialsProvider:
    @patch("fastmcp_creds.keyring._keyring")
    def test_returns_credentials_from_keyring(self, mock_keyring):
        mock_keyring.get_password.side_effect = lambda service, key: (
            "alice" if key == "username" else "secret"
        )
        provider = KeyringCredentialsProvider("my-service")
        assert provider.get_credentials() == ("alice", "secret")

    @patch("fastmcp_creds.keyring._keyring")
    def test_custom_keys(self, mock_keyring):
        mock_keyring.get_password.side_effect = lambda service, key: (
            "alice" if key == "login" else "secret" if key == "token" else None
        )
        provider = KeyringCredentialsProvider(
            "my-service", username_key="login", password_key="token"
        )
        assert provider.get_credentials() == ("alice", "secret")

    @patch("fastmcp_creds.keyring._keyring")
    def test_missing_entry_returns_none(self, mock_keyring):
        mock_keyring.get_password.return_value = None
        provider = KeyringCredentialsProvider("my-service")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.keyring._keyring")
    def test_partial_entry_returns_none(self, mock_keyring):
        mock_keyring.get_password.side_effect = lambda service, key: (
            "alice" if key == "username" else None
        )
        provider = KeyringCredentialsProvider("my-service")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.keyring._keyring")
    def test_correct_service_name_used(self, mock_keyring):
        mock_keyring.get_password.return_value = None
        KeyringCredentialsProvider("douane-portal").get_credentials()
        calls = mock_keyring.get_password.call_args_list
        assert all(call.args[0] == "douane-portal" for call in calls)

    @patch("fastmcp_creds.keyring._keyring")
    def test_token_mode_returns_token_for_both_positions(self, mock_keyring):
        mock_keyring.get_password.return_value = "tok-abc123"
        provider = KeyringCredentialsProvider.for_token("my-service")
        assert provider.get_credentials() == ("tok-abc123", "tok-abc123")
        mock_keyring.get_password.assert_called_once_with("my-service", "token")

    @patch("fastmcp_creds.keyring._keyring")
    def test_token_mode_returns_none_when_missing(self, mock_keyring):
        mock_keyring.get_password.return_value = None
        provider = KeyringCredentialsProvider.for_token("my-service")
        assert provider.get_credentials() == (None, None)

    @patch("fastmcp_creds.keyring._keyring")
    def test_token_mode_custom_key(self, mock_keyring):
        mock_keyring.get_password.return_value = "tok-abc123"
        provider = KeyringCredentialsProvider.for_token("my-service", token_key="jwt")
        provider.get_credentials()
        mock_keyring.get_password.assert_called_once_with("my-service", "jwt")
