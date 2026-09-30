import logging
import threading

try:
    import keyring as _keyring
except ImportError as e:
    raise ImportError(
        "keyring is required for KeyringCredentialsProvider. "
        "Install it with: pip install fastmcp-creds[keyring]"
    ) from e

logger = logging.getLogger(__name__)

# A hung OS keychain call (e.g. a locked keychain waiting for an unlock prompt
# that never appears in a headless session) must not stall the MCP server's
# startup handshake forever: the client has no visibility into why the server
# never responds.
DEFAULT_KEYRING_TIMEOUT = 5.0


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

    The keychain lookup is bounded by ``timeout`` seconds (default 5). When the
    keychain does not answer in time, a warning is logged and no credentials are
    returned, so a provider chain falls through to its next provider. Pass
    ``timeout=None`` to wait indefinitely.
    """

    def __init__(
        self,
        service: str,
        username_key: str = "username",
        password_key: str = "password",
        timeout: float | None = DEFAULT_KEYRING_TIMEOUT,
    ):
        self.service = service
        self.username_key: str | None = username_key
        self.password_key = password_key
        self.timeout = timeout

    @classmethod
    def for_token(
        cls,
        service: str,
        token_key: str = "token",
        timeout: float | None = DEFAULT_KEYRING_TIMEOUT,
    ) -> "KeyringCredentialsProvider":
        """Create a token-mode provider that reads a single keyring entry."""
        instance = cls.__new__(cls)
        instance.service = service
        instance.username_key = None
        instance.password_key = token_key
        instance.timeout = timeout
        return instance

    def get_credentials(self) -> tuple[str | None, str | None]:
        if self.timeout is None:
            return self._read_credentials()

        # The keyring API is synchronous and cannot be cancelled, so run it in a
        # daemon thread and stop waiting after the timeout. A thread left hanging
        # in the keychain does not keep the process alive on exit.
        outcome: dict = {}

        def read() -> None:
            try:
                outcome["result"] = self._read_credentials()
            except BaseException as e:
                outcome["error"] = e

        thread = threading.Thread(
            target=read, name=f"keyring-{self.service}", daemon=True
        )
        thread.start()
        thread.join(self.timeout)
        if thread.is_alive():
            logger.warning(
                f"Keyring service '{self.service}' did not respond within {self.timeout}s, skipping it"
            )
            return None, None
        if "error" in outcome:
            raise outcome["error"]
        return outcome["result"]

    def _read_credentials(self) -> tuple[str | None, str | None]:
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
