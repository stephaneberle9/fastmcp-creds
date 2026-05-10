import logging

try:
    import keyring as _keyring
except ImportError as e:
    raise ImportError(
        "keyring is required for KeyringCredentialsProvider. "
        "Install it with: pip install fastmcp-creds[keyring]"
    ) from e

logger = logging.getLogger(__name__)


class KeyringCredentialsProvider:
    """Provider for credentials stored in the OS keychain via keyring.

    Two-key mode (username + password stored under separate account keys)::

        KeyringCredentialsProvider("my-service")
        # reads: keyring get my-service username
        #        keyring get my-service password

    Token mode (single keyring entry stored under the password key)::

        KeyringCredentialsProvider.for_token("my-service")
        # reads: keyring get my-service token

    Or with a custom key name::

        KeyringCredentialsProvider.for_token("my-service", token_key="jwt")
        # reads: keyring get my-service jwt
    """

    def __init__(
        self,
        service: str,
        username_key: str = "username",
        password_key: str = "password",
    ):
        self.service = service
        self.username_key = username_key
        self.password_key = password_key

    @classmethod
    def for_token(
        cls, service: str, token_key: str = "token"
    ) -> "KeyringCredentialsProvider":
        """Create a token-mode provider that reads a single keyring entry."""
        instance = cls.__new__(cls)
        instance.service = service
        instance.username_key = None
        instance.password_key = token_key
        return instance

    def get_credentials(self) -> tuple[str | None, str | None]:
        if self.username_key is None:
            logger.debug(f"Reading token from keyring service '{self.service}'")
            token = _keyring.get_password(self.service, self.password_key)
            if token:
                logger.debug(
                    f"Successfully retrieved token '{token[:7]}***' from keyring service '{self.service}'"
                )
                return token, token
            logger.debug(f"No token found in keyring service '{self.service}'")
            return None, None

        logger.debug(f"Reading credentials from keyring service '{self.service}'")
        username = _keyring.get_password(self.service, self.username_key)
        password = _keyring.get_password(self.service, self.password_key)
        if username and password:
            logger.debug(
                f"Successfully retrieved credentials for '{username[:7]}***' from keyring service '{self.service}'"
            )
            return username, password
        logger.debug(f"No credentials found in keyring service '{self.service}'")
        return None, None
