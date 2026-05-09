import base64
import binascii
import logging
import re

from fastmcp.server.dependencies import get_http_headers

logger = logging.getLogger(__name__)


def is_unresolved_placeholder_value(value: str) -> bool:
    """Detect whether a header value is an unresolved env-var or template placeholder.

    MCP clients that support variable substitution (e.g. Claude Desktop) expand
    ${VAR_NAME} tokens in their config before sending HTTP headers. When a referenced
    variable is not defined or the client skips substitution, the literal placeholder
    string (e.g. "${MY_VAR}" or "Basic ${MY_VAR}") arrives in the header instead of
    real credentials. This function identifies those cases so callers can treat the
    header as absent rather than attempting to parse garbage as base64.
    """
    if not value:
        return False
    # Entire value is a bare unresolved placeholder, e.g. "${MANGO_BASIC_AUTH}"
    if re.match(r"^\$\{.*\}$", value):
        logger.warning(f"Detected unresolved placeholder in header: {value}")
        return True
    # Scheme prefix was expanded but the credential token was not, e.g. "Basic ${MY_CREDS}"
    if re.match(r"^(Bearer\s+)?Basic\s+\$\{.*\}$", value):
        logger.warning(f"Detected unresolved placeholder in basic auth header: {value}")
        return True
    return False


class BasicAuthError(Exception):
    """Raised when Basic Auth credential extraction from an HTTP header fails."""

    def __init__(self, message: str, header_name: str):
        super().__init__(message)
        self.header_name = header_name

    def __str__(self):
        return f"Failed to extract basic auth credentials from '{self.header_name}' header: {super().__str__()}"


class BasicAuthCredentialsProvider:
    """Provider that extracts credentials from an HTTP Basic Auth header.

    Checks the optional custom header first, then falls back to the standard
    ``Authorization`` header. Accepts ``Basic <base64>``, raw base64, and the
    non-compliant ``Bearer Basic <base64>`` variant emitted by MCP Inspector.
    """

    def __init__(self, custom_header_name: str | None = None):
        self.custom_header_name = custom_header_name

    def _parse_basic_auth_header(self, header_name: str, header_value: str) -> tuple[str | None, str | None]:
        if not header_value:
            return None, None

        # Accept "Basic <b64>", "Bearer Basic <b64>" (MCP Inspector), or raw base64
        match = re.match(r"^(Bearer[ \t]+)?Basic[ \t]+(.+)$", header_value)
        if match:
            encoded_credentials = match.group(2)
        else:
            match = re.match(r"^(Bearer[ \t]+)?([A-Za-z0-9+/=]+)$", header_value)
            if match:
                encoded_credentials = match.group(2)
            else:
                if " " in header_value or "\t" in header_value:
                    scheme = header_value.split()[0]
                    raise BasicAuthError(f"Unsupported scheme '{scheme}', only 'Basic' is supported", header_name)
                else:
                    raise BasicAuthError(
                        "Expected 'Basic <base64-encoded credentials string>' or '<base64-encoded credentials string>'",
                        header_name,
                    )

        if not encoded_credentials:
            raise BasicAuthError("Missing base64-encoded credentials string", header_name)

        try:
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as e:
            raise BasicAuthError(f"Failed to decode base64-encoded credentials string: {e}", header_name)

        if ":" not in decoded_credentials:
            raise BasicAuthError("Invalid credentials string - missing colon separator", header_name)

        username, password = decoded_credentials.split(":", 1)
        if not username or not password:
            raise BasicAuthError("Invalid credentials string - empty username or password", header_name)

        return username, password

    def get_credentials(self) -> tuple[str | None, str | None]:
        try:
            headers = get_http_headers()

            if self.custom_header_name:
                value = headers.get(self.custom_header_name.lower()) or headers.get(self.custom_header_name)
                if value:
                    if is_unresolved_placeholder_value(value):
                        logger.debug(f"Ignoring unresolved placeholder in '{self.custom_header_name}' header")
                        return None, None
                    logger.debug(f"Extracting basic auth credentials from '{self.custom_header_name}' header")
                    try:
                        return self._parse_basic_auth_header(self.custom_header_name, value)
                    except BasicAuthError:
                        pass  # fall through to standard Authorization header

            value = headers.get("authorization") or headers.get("Authorization")
            if value:
                if is_unresolved_placeholder_value(value):
                    logger.debug("Ignoring unresolved placeholder in 'Authorization' header")
                    return None, None
                logger.debug("Extracting basic auth credentials from 'Authorization' header")
                try:
                    return self._parse_basic_auth_header("Authorization", value)
                except BasicAuthError:
                    pass

            logger.debug("No valid Basic Auth header found")
            return None, None
        except Exception as e:
            logger.error(f"Failed to retrieve credentials from authorization headers: {e}")
            return None, None
