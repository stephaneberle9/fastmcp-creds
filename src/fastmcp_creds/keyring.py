"""Re-exported from credchain, where the framework-neutral providers live."""

try:
    from credchain.keyring import DEFAULT_KEYRING_TIMEOUT, KeyringCredentialsProvider
except ImportError as e:
    raise ImportError(
        "keyring is required for KeyringCredentialsProvider. "
        "Install it with: pip install fastmcp-creds[keyring]"
    ) from e

__all__ = ["DEFAULT_KEYRING_TIMEOUT", "KeyringCredentialsProvider"]
