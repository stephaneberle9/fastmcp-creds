import logging
import os

logger = logging.getLogger(__name__)


class EnvironmentCredentialsProvider:
    """Provider for credentials from environment variables.

    Two-var mode (username + password)::

        EnvironmentCredentialsProvider("MY_USERNAME", "MY_PASSWORD")

    Token mode (single env var)::

        EnvironmentCredentialsProvider.for_token("MY_TOKEN")
    """

    def __init__(self, username_env_var_name: str, password_env_var_name: str):
        self.username_env_var_name = username_env_var_name
        self.password_env_var_name = password_env_var_name

    @classmethod
    def for_token(cls, token_env_var_name: str) -> "EnvironmentCredentialsProvider":
        """Create a token-mode provider that reads a single environment variable."""
        instance = cls.__new__(cls)
        instance.username_env_var_name = None
        instance.password_env_var_name = token_env_var_name
        return instance

    def get_credentials(self) -> tuple[str | None, str | None]:
        if self.username_env_var_name is None:
            logger.debug("Reading token from environment variable")
            token = os.environ.get(self.password_env_var_name)
            if token:
                logger.debug(
                    f"Successfully retrieved token '{token[:7]}***' from environment variable"
                )
                return token, token
            logger.debug("No token found in environment variable")
            return None, None

        logger.debug("Reading credentials from environment variables")
        username = os.environ.get(self.username_env_var_name)
        password = os.environ.get(self.password_env_var_name)
        if username and password:
            logger.debug(
                f"Successfully retrieved credentials for '{username[:7]}***' from environment variables"
            )
            return username, password
        logger.debug("No credentials found in environment variables")
        return None, None
