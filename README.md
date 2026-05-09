# fastmcp-creds <!-- omit in toc -->

Pluggable credential management for FastMCP servers — supply API tokens or
username/password credentials for the backend services they connect to, from
environment variables, OS keychain, or HTTP headers, with automatic fallback
through a priority chain.

- [Installation](#installation)
- [Usage](#usage)
  - [Credential provider chain](#credential-provider-chain)
  - [Environment variables](#environment-variables)
  - [HTTP Basic Auth header](#http-basic-auth-header)
  - [Custom HTTP headers](#custom-http-headers)
  - [OS keychain](#os-keychain)
- [API Reference](#api-reference)
  - [`CredentialsProvider`](#credentialsprovider)
  - [`CredentialsProviderChain`](#credentialsproviderchain)
  - [`EnvironmentCredentialsProvider`](#environmentcredentialsprovider)
  - [`BasicAuthCredentialsProvider`](#basicauthcredentialsprovider)
  - [`CustomHeaderCredentialsProvider`](#customheadercredentialsprovider)
  - [`KeyringCredentialsProvider`](#keyringcredentialsprovider)
  - [`BasicAuthError`](#basicautherror)
  - [`is_unresolved_placeholder_value`](#is_unresolved_placeholder_value)
- [Contributing](#contributing)
- [License](#license)

## Installation

```bash
pip install fastmcp-creds
# or, with uv:
uv add fastmcp-creds
```

The `KeyringCredentialsProvider` requires the optional `keyring` extra:

```bash
pip install fastmcp-creds[keyring]
# or, with uv:
uv add fastmcp-creds[keyring]
```

Requires Python 3.10+.

## Usage

### Credential provider chain

Compose providers in priority order. The chain tries each in sequence and
returns the first result where both username and password (or token) are
non-empty.

```python
from fastmcp_creds import (
    CredentialsProviderChain,
    BasicAuthCredentialsProvider,
    EnvironmentCredentialsProvider,
)
from fastmcp_creds.keyring import KeyringCredentialsProvider  # optional dep

chain = CredentialsProviderChain([
    KeyringCredentialsProvider("my-service"),
    BasicAuthCredentialsProvider(),
    EnvironmentCredentialsProvider("MY_USERNAME", "MY_PASSWORD"),
])

username, password = chain.get_credentials()
```

### Environment variables

Read username and password from two environment variables:

```python
from fastmcp_creds import EnvironmentCredentialsProvider

provider = EnvironmentCredentialsProvider("MY_USERNAME", "MY_PASSWORD")
username, password = provider.get_credentials()
```

For a single token variable:

```python
provider = EnvironmentCredentialsProvider.for_token("MY_API_TOKEN")
token, _ = provider.get_credentials()
```

### HTTP Basic Auth header

Decode credentials from the standard `Authorization: Basic <base64>` header.
Also accepts the non-compliant `Bearer Basic <base64>` variant emitted by MCP
Inspector, and raw base64 without a scheme prefix.

```python
from fastmcp_creds import BasicAuthCredentialsProvider

provider = BasicAuthCredentialsProvider()
username, password = provider.get_credentials()
```

Optionally check a custom header first before falling back to `Authorization`:

```python
provider = BasicAuthCredentialsProvider(custom_header_name="X-My-Auth")
```

### Custom HTTP headers

Read credentials from two plain-text HTTP headers:

```python
from fastmcp_creds import CustomHeaderCredentialsProvider

provider = CustomHeaderCredentialsProvider("X-Username", "X-Password")
username, password = provider.get_credentials()
```

For a single token header:

```python
provider = CustomHeaderCredentialsProvider.for_token("X-Api-Token")
token, _ = provider.get_credentials()
```

### OS keychain

Read credentials stored in the OS keychain via
[`keyring`](https://pypi.org/project/keyring/). Requires `fastmcp-creds[keyring]`.

```python
from fastmcp_creds.keyring import KeyringCredentialsProvider

# Two-key mode: reads "username" and "password" entries under the service name
provider = KeyringCredentialsProvider("my-service")
username, password = provider.get_credentials()

# Token mode: reads a single "token" entry
provider = KeyringCredentialsProvider.for_token("my-service")
token, _ = provider.get_credentials()

# Custom key names
provider = KeyringCredentialsProvider("my-service", username_key="user", password_key="secret")
provider = KeyringCredentialsProvider.for_token("my-service", token_key="jwt")
```

## API Reference

### `CredentialsProvider`

`CredentialsProvider` is a `Protocol` — any object with a
`get_credentials() -> tuple[str | None, str | None]` method satisfies it.

### `CredentialsProviderChain`

`CredentialsProviderChain(providers)` — tries each provider in order and
returns the first result where both values are non-empty. Returns
`(None, None)` if no provider succeeds.

| Method | Description |
| --- | --- |
| `get_credentials()` | Returns `tuple[str \| None, str \| None]` — `(username, password)` or `(token, token)` |

### `EnvironmentCredentialsProvider`

`EnvironmentCredentialsProvider(username_env_var_name, password_env_var_name)`
— reads two environment variables.

`EnvironmentCredentialsProvider.for_token(token_env_var_name)` — reads a
single environment variable; returns it as both elements of the tuple.

| Method | Description |
| --- | --- |
| `get_credentials()` | Returns `tuple[str \| None, str \| None]` |

### `BasicAuthCredentialsProvider`

`BasicAuthCredentialsProvider(custom_header_name=None)` — extracts credentials
from an HTTP Basic Auth header. Checks `custom_header_name` first if provided,
then falls back to the standard `Authorization` header. Silently ignores
unresolved MCP client placeholders (e.g. `${MY_VAR}`).

| Method | Description |
| --- | --- |
| `get_credentials()` | Returns `tuple[str \| None, str \| None]`; raises `BasicAuthError` on malformed headers |

### `CustomHeaderCredentialsProvider`

`CustomHeaderCredentialsProvider(username_header_name, password_header_name)`
— reads credentials from two plain-text HTTP headers. Ignores unresolved
placeholders.

`CustomHeaderCredentialsProvider.for_token(token_header_name)` — reads a
single header; returns it as both elements of the tuple.

| Method | Description |
| --- | --- |
| `get_credentials()` | Returns `tuple[str \| None, str \| None]` |

### `KeyringCredentialsProvider`

`KeyringCredentialsProvider(service, username_key="username", password_key="password")`
— reads credentials stored in the OS keychain under the given service name.
Requires `fastmcp-creds[keyring]`.

`KeyringCredentialsProvider.for_token(service, token_key="token")` — reads a
single keychain entry.

| Method | Description |
| --- | --- |
| `get_credentials()` | Returns `tuple[str \| None, str \| None]` |

### `BasicAuthError`

`BasicAuthError(message, header_name)` — raised by `BasicAuthCredentialsProvider`
when a header is present but malformed (bad base64, unsupported scheme, missing
colon separator, empty username or password).

| Field | Type | Description |
| --- | --- | --- |
| `header_name` | `str` | Name of the header that caused the error |

### `is_unresolved_placeholder_value`

`is_unresolved_placeholder_value(value: str) -> bool` — returns `True` when a
header value is an unresolved MCP client placeholder such as `${MY_VAR}` or
`Basic ${MY_VAR}`. Used internally by `BasicAuthCredentialsProvider` and
`CustomHeaderCredentialsProvider`; exposed for custom provider implementations.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT — see [LICENSE](LICENSE).
