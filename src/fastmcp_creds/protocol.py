from typing import Protocol


class CredentialsProvider(Protocol):
    def get_credentials(self) -> tuple[str | None, str | None]: ...
