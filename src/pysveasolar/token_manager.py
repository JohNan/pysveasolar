import logging
from abc import ABC, abstractmethod
from datetime import datetime

import jwt

_LOGGER = logging.getLogger(__name__)


class TokenManager(ABC):
    """Token manager class."""

    @abstractmethod
    def __init__(self, access_token: str, refresh_token: str):
        """Initialize the token manager."""
        self._refresh_token = ""
        self._access_token = ""
        self.update(access_token, refresh_token)

    @property
    def access_token(self) -> str:
        """Return the access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str:
        """Return the refresh token."""
        return self._refresh_token

    @abstractmethod
    def update(self, access_token: str, refresh_token: str):
        """Update the tokens."""
        self._access_token = access_token
        self._refresh_token = refresh_token

    def ensure_credentials(self) -> bool:
        """Check if the token manager has credentials."""
        if self._access_token == "":
            _LOGGER.error("Access Token is missing")
            return False
        if self._refresh_token == "":
            _LOGGER.error("Refresh Token is missing")
            return False
        return True

    def is_token_valid(self) -> bool:
        """Check token validity"""
        try:
            payload = jwt.decode(self.access_token, options={"verify_signature": False})
            minutes_until_expiry = (
                datetime.fromtimestamp(payload["exp"]) - datetime.now()
            ).total_seconds() / 60
            if minutes_until_expiry < 10:
                _LOGGER.info(
                    "Access Token is about to expire in %s minutes, refreshing it",
                    minutes_until_expiry,
                )
                return False
            return True
        except jwt.ExpiredSignatureError as e:
            _LOGGER.error("Access Token is invalid - %s", e)
            return False
