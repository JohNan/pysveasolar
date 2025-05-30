import logging
from typing import Callable

from aiohttp import ClientResponse, ClientSession

_LOGGER = logging.getLogger(__name__)


class Auth:
    """Class to make authenticated requests."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        async_get_access_token: Callable,
    ):
        """Initialize the auth."""
        self.session = session
        self.host = host
        self.async_get_access_token = async_get_access_token

    async def request(self, method: str, path: str, **kwargs) -> ClientResponse:
        """Make a request."""
        json = kwargs.get("json", None)
        headers = kwargs.get("headers")

        if headers is None:
            headers = {}
        else:
            headers = dict(headers)

        if not kwargs.get("skip_auth_headers", None):
            try:
                access_token = await self.async_get_access_token()
                headers["authorization"] = f"Bearer {access_token}"
            except Exception as e:
                _LOGGER.error(f"Failed to get access token: {e}")
                raise e

        return await self.session.request(
            method, f"{self.host}/{path}", headers=headers, json=json
        )

    async def connect_to_websocket(self, uri, connected_callback=None):
        access_token = await self.async_get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        websocket = await self.session.ws_connect(uri, headers=headers, heartbeat=55)
        _LOGGER.debug(f"Connected to the WebSocket at {uri}")
        if connected_callback is not None:
            connected_callback()
        return websocket
