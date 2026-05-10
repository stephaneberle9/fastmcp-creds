"""fastmcp-creds: credential provider chain for FastMCP servers.

Providers (import directly):
    CredentialsProviderChain  — tries providers in order until one succeeds
    EnvironmentCredentialsProvider  — reads from env vars
    BasicAuthCredentialsProvider    — reads from Authorization / custom Basic Auth header
    CustomHeaderCredentialsProvider — reads from two separate plain-text headers
    KeyringCredentialsProvider      — reads from OS keychain (requires fastmcp-creds[keyring])

Usage::

    from fastmcp_creds import CredentialsProviderChain, BasicAuthCredentialsProvider, EnvironmentCredentialsProvider
    from fastmcp_creds.keyring import KeyringCredentialsProvider  # optional dep

    chain = CredentialsProviderChain([
        KeyringCredentialsProvider("my-service"),
        BasicAuthCredentialsProvider(),
        EnvironmentCredentialsProvider("MY_USERNAME", "MY_PASSWORD"),
    ])
    username, password = chain.get_credentials()
"""

from importlib.metadata import PackageNotFoundError, version

from .basic_auth import (
    BasicAuthCredentialsProvider,
    BasicAuthError,
    is_unresolved_placeholder_value,
)
from .chain import CredentialsProviderChain
from .env import EnvironmentCredentialsProvider
from .header import CustomHeaderCredentialsProvider
from .protocol import CredentialsProvider

try:
    __version__ = version("fastmcp_creds")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

__all__ = [
    "CredentialsProvider",
    "CredentialsProviderChain",
    "EnvironmentCredentialsProvider",
    "BasicAuthCredentialsProvider",
    "BasicAuthError",
    "is_unresolved_placeholder_value",
    "CustomHeaderCredentialsProvider",
]
