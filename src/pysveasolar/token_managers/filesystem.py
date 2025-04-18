import json
from pathlib import Path

from pysveasolar.token_manager import TokenManager


class TokenManagerFileSystem(TokenManager):
    """Token manager class, with filesystem based persistent storage."""

    def __init__(self, storage_file: Path | None = None):
        """Initialize the token manager."""
        if storage_file is not None:
            self._storage_file = storage_file
        else:
            self._storage_file = Path.home() / ".cache" / "pysveasolar" / "credentials"

        # Make sure that the parent directory exists
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)

    def update(self, access_token: str, refresh_token: str):
        """Update the tokens."""
        super().update(access_token, refresh_token)
        self.save()

    def save(self):
        """Save the tokens to filesystem."""
        with open(self._storage_file, "w") as f:
            json.dump(
                {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                },
                f,
            )

    def load(self):
        """Load the tokens from filesystem."""
        with open(self._storage_file) as f:
            credentials = json.load(f)
            self.update(
                credentials.get("access_token"),
                credentials.get("refresh_token"),
            )
