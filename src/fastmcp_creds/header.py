import logging

from fastmcp.server.dependencies import get_http_headers

from .basic_auth import is_unresolved_placeholder_value

logger = logging.getLogger(__name__)


class CustomHeaderCredentialsProvider:
    """Provider for credentials passed as plain-text HTTP headers.

    Two-header mode (username + password)::

        CustomHeaderCredentialsProvider("X-Username", "X-Password")

    Token mode (single header)::

        CustomHeaderCredentialsProvider.for_token("X-Token")
    """

    def __init__(self, username_header_name: str, password_header_name: str):
        self.username_header_name = username_header_name
        self.password_header_name = password_header_name

    @classmethod
    def for_token(cls, token_header_name: str) -> "CustomHeaderCredentialsProvider":
        """Create a token-mode provider that reads a single HTTP header."""
        instance = cls.__new__(cls)
        instance.username_header_name = None
        instance.password_header_name = token_header_name
        return instance

    def get_credentials(self) -> tuple[str | None, str | None]:
        try:
            headers = get_http_headers()

            if self.username_header_name is None:
                token = headers.get(self.password_header_name.lower()) or headers.get(
                    self.password_header_name
                )
                if token and is_unresolved_placeholder_value(token):
                    logger.debug(
                        f"Ignoring unresolved placeholder in '{self.password_header_name}' header"
                    )
                    token = None
                if token:
                    logger.debug(
                        f"Successfully extracted token '{token[:7]}***' from {self.password_header_name} header"
                    )
                    return token, token
                logger.debug(f"No valid '{self.password_header_name}' header found")
                return None, None

            username = headers.get(self.username_header_name.lower()) or headers.get(
                self.username_header_name
            )
            password = headers.get(self.password_header_name.lower()) or headers.get(
                self.password_header_name
            )

            if username and is_unresolved_placeholder_value(username):
                logger.debug(
                    f"Ignoring unresolved placeholder in '{self.username_header_name}' header"
                )
                username = None
            if password and is_unresolved_placeholder_value(password):
                logger.debug(
                    f"Ignoring unresolved placeholder in '{self.password_header_name}' header"
                )
                password = None

            if username and password:
                logger.debug(
                    f"Successfully extracted credentials for '{username[:7]}***' from {self.username_header_name} and {self.password_header_name} headers"
                )
                return username, password
            logger.debug(
                f"No valid '{self.username_header_name}' and '{self.password_header_name}' headers found"
            )
            return None, None
        except Exception as e:
            logger.error(f"Failed to retrieve credentials from custom headers: {e}")
            return None, None
