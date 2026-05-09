import logging

from .protocol import CredentialsProvider

logger = logging.getLogger(__name__)


class CredentialsProviderChain:
    """Chain of credentials providers invoked in priority order until one succeeds."""

    def __init__(self, providers: list[CredentialsProvider]):
        self.providers = providers

    def get_credentials(self) -> tuple[str | None, str | None]:
        logger.debug("Retrieving credentials using credentials provider chain...")
        for i, provider in enumerate(self.providers):
            try:
                logger.debug(f"Trying provider {i + 1}/{len(self.providers)}: {provider.__class__.__name__}...")
                username, password = provider.get_credentials()
                if username and password:
                    logger.debug(f"Successfully retrieved credentials for '{username[:7]}***' from {provider.__class__.__name__}")
                    return username, password
                else:
                    logger.debug(f"No credentials found from {provider.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error retrieving credentials from {provider.__class__.__name__}: {e}")
        logger.debug("No credentials found from any provider in the chain")
        return None, None
