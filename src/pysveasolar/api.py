import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Callable

from aiohttp import ClientSession, ClientError
from dataclass_wizard import fromdict

from pysveasolar.auth import Auth
from pysveasolar.models import BadgesUpdatedMessage, KeepAliveMessage, VehicleDetailsUpdatedMessage, Location, \
    BatteryDetailsData, BadgesUpdatedData, Badge
from pysveasolar.token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)


class SveaSolarAPI:
    """Class to communicate with the ExampleHub API."""

    def __init__(self, session: ClientSession, token_manager: TokenManager):
        """Initialize the API and store the auth so we can make requests."""
        self.token_manager = token_manager
        self.session = session

        self.auth = Auth(
            session,
            "https://prod.app.sveasolar.com/api",
            self.async_get_access_token,
        )

    async def async_login(self, username: str, password: str):
        try:
            response = await self.auth.request(
                "post",
                "v1/auth/login-with-email",
                json={"email": username, "password": password},
                skip_auth_headers=True
            )
            response.raise_for_status()
        except Exception as e:
            _LOGGER.exception("Failed to login to Svea Solar")
            raise ClientError("Failed to login to Svea Solar") from e

        data = await response.json()
        self.token_manager.update(data["accessToken"], data["refreshToken"])
        _LOGGER.info("Successfully logged in to Svea Solar")

    async def async_get_access_token(self) -> str:
        if self.token_manager.is_token_valid():
            return self.token_manager.access_token

        try:
            _LOGGER.debug("Refreshing access token")
            response = await self.auth.request(
                "post",
                "v1/auth/refresh-access-token",
                json={"refreshToken": self.token_manager.refresh_token},
                skip_auth_headers=True,
            )

            response.raise_for_status()
        except Exception as e:
            raise ValueError(f"Failed to get access token: {e}")

        data = await response.json()
        self.token_manager.update(data["accessToken"], self.token_manager.refresh_token)

        return self.token_manager.access_token

    async def async_get_my_data(self) -> List[Location]:
        """Return the locations."""
        resp = await self.auth.request("get", "v2/my-data?timezone=Europe%2FStockholm")
        resp.raise_for_status()
        data = await resp.json()
        return [fromdict(Location, location) for location in data]

    async def async_get_my_system(self):
        """Return the appliances."""
        resp = await self.auth.request("get", "v2/my-system")
        resp.raise_for_status()
        return await resp.json()

    async def async_get_user(self):
        """Return the appliances."""
        resp = await self.auth.request("get", "v1/user")
        resp.raise_for_status()
        return await resp.json()

    async def async_get_dashboard(self):
        resp = await self.auth.request("get", "v2/dashboard/performance/summary")
        resp.raise_for_status()
        return await resp.json()

    async def async_get_details(self, location_id: str):
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = today + timedelta(days=7)
        resp = await self.auth.request("get",
                                       f"v2/dashboard/performance/details/location/{location_id}?fromDate={self.format_date(start_of_week)}&toDate={self.format_date(end_of_week)}&resolution=DAY")
        resp.raise_for_status()
        return await resp.json()

    async def async_get_battery(self, battery_id: str) -> BatteryDetailsData:
        resp = await self.auth.request("get", f"v1/battery/{battery_id}/details")
        resp.raise_for_status()
        data = await resp.json()
        return fromdict(BatteryDetailsData,data)

    async def async_home_websocket(self, data_callback: Callable[[BadgesUpdatedMessage], None], connected_callback=None, json_data_callback=None,
                                   keep_alive_callback=None):
        uri = "wss://prod.app.sveasolar.com/api/v1/ws/home"
        async with await self.auth.connect_to_websocket(uri, connected_callback) as websocket:
            async for message in websocket:
                try:
                    if json_data_callback is not None:
                        json_data_callback(message.data)

                    data = message.json()
                    if data["type"] == "BadgesUpdated":
                        data_callback(fromdict(BadgesUpdatedMessage, data))
                    elif data["type"] == "KeepAlive":
                        if keep_alive_callback is not None:
                            keep_alive_callback(fromdict(KeepAliveMessage, data))
                    else:
                        _LOGGER.warning(f"Unknown message type: {data['type']}")
                        continue
                except Exception as e:
                    _LOGGER.error(f"Failed to parse message: {e} - {message.data}")

    async def async_ev_websocket(self, ev_id: str, data_callback: Callable[[VehicleDetailsUpdatedMessage], None], connected_callback=None, json_data_callback=None,
                                 keep_alive_callback=None):
        uri = f"wss://prod.app.sveasolar.com/api/v1/ws/electric-vehicle/{ev_id}"
        async with await self.auth.connect_to_websocket(uri, connected_callback) as websocket:
            async for message in websocket:
                try:
                    if json_data_callback is not None:
                        json_data_callback(message.data)

                    data = message.json()
                    if data["type"] == "VehicleDetailsUpdated":
                        data_callback(fromdict(VehicleDetailsUpdatedMessage, data))
                    elif data["type"] == "KeepAlive":
                        if keep_alive_callback is not None:
                            keep_alive_callback(fromdict(KeepAliveMessage, data))
                    else:
                        _LOGGER.warning(f"Unknown message type: {data['type']}")
                        continue
                except Exception as e:
                    _LOGGER.error(f"Failed to parse message: {e} - {message.data}")

    @staticmethod
    def format_date(dt):
        iso_format = dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601-format
        return urllib.parse.quote(iso_format)
