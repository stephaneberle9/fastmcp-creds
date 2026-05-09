from unittest.mock import Mock

from fastmcp_creds import CredentialsProviderChain


class TestCredentialsProviderChain:
    def test_first_provider_succeeds(self):
        p1 = Mock()
        p1.get_credentials.return_value = ("user1", "pass1")
        p2 = Mock()
        chain = CredentialsProviderChain([p1, p2])
        assert chain.get_credentials() == ("user1", "pass1")
        p2.get_credentials.assert_not_called()

    def test_falls_back_to_second_provider(self):
        p1 = Mock()
        p1.get_credentials.return_value = (None, None)
        p2 = Mock()
        p2.get_credentials.return_value = ("user2", "pass2")
        chain = CredentialsProviderChain([p1, p2])
        assert chain.get_credentials() == ("user2", "pass2")

    def test_partial_credentials_not_accepted(self):
        p1 = Mock()
        p1.get_credentials.return_value = ("user1", None)
        p2 = Mock()
        p2.get_credentials.return_value = ("user2", "pass2")
        chain = CredentialsProviderChain([p1, p2])
        assert chain.get_credentials() == ("user2", "pass2")

    def test_empty_provider_list(self):
        assert CredentialsProviderChain([]).get_credentials() == (None, None)

    def test_failing_provider_does_not_break_chain(self):
        bad = Mock()
        bad.get_credentials.side_effect = Exception("boom")
        good = Mock()
        good.get_credentials.return_value = ("u", "p")
        chain = CredentialsProviderChain([bad, good])
        assert chain.get_credentials() == ("u", "p")

    def test_all_providers_fail(self):
        p1 = Mock()
        p1.get_credentials.return_value = (None, None)
        p2 = Mock()
        p2.get_credentials.return_value = (None, None)
        assert CredentialsProviderChain([p1, p2]).get_credentials() == (None, None)
