from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class BatteryDetailsData:
    id: str
    dischargePower: int
    status: str
    stateOfCharge: int
    chargedEnergy: float
    dischargedEnergy: float
    locationName: str
    locationId: str
    brand: str
    name: str
    imageUrl: str
    capacity: str
    chemistry: str
    typeOfBattery: str


class Battery:
    battery_id: str
    name: str
    status: str
    state_of_charge: Optional[float]
    image_url: Optional[str]

    def __init__(
        self,
        battery_id: str,
        name: str,
        status: str,
        state_of_charge: Optional[float],
        image_url: Optional[str],
    ):
        self.battery_id = battery_id
        self.name = name
        self.status = status
        self.state_of_charge = state_of_charge
        self.image_url = image_url


class Ev:
    ev_id: str
    name: str
    status: str
    range_in_km: float
    image_url: Optional[str]

    def __init__(
        self,
        ev_id: str,
        name: str,
        status: str,
        range_in_km: int,
        image_url: Optional[str],
    ):
        self.ev_id = ev_id
        self.name = name
        self.status = status
        self.range_in_km = range_in_km
        self.image_url = image_url


@dataclass
class Badge:
    id: str
    type: str
    status: str
    subtitle: dict
    title: str
    progress: float
    imageUrl: Optional[str]


@dataclass
class BadgesUpdatedData:
    badges: List[Badge]

    @property
    def has_battery(self):
        return any(badge.type == "Battery" for badge in self.badges)

    @property
    def has_ev(self):
        return any(badge.type == "Ev" for badge in self.badges)

    @property
    def ev(self) -> Optional[Ev]:
        if not self.has_ev:
            return None

        ev: Badge = next(badge for badge in self.badges if badge.type == "Ev")
        if ev is None:
            return None

        return Ev(
            ev_id=ev.id,
            name=ev.title,
            status=ev.status,
            range_in_km=ev.subtitle["value"],
            image_url=ev.imageUrl,
        )

    @property
    def battery(self) -> Optional[Battery]:
        if not self.has_battery:
            return None

        battery: Badge = next(badge for badge in self.badges if badge.type == "Battery")
        if battery is None:
            return None

        if battery.subtitle["key"] == "stateOfCharge":
            return Battery(
                battery_id=battery.id,
                name=battery.title,
                status=battery.status,
                state_of_charge=battery.subtitle["value"],
                image_url=battery.imageUrl,
            )

        return Battery(
            battery_id=battery.id,
            name=battery.title,
            status=battery.status,
            state_of_charge=None,
            image_url=battery.imageUrl,
        )


@dataclass
class BadgesUpdatedMessage:
    id: str
    type: str
    data: BadgesUpdatedData
    time: datetime
    dataContentType: str
    source: str
    traceParent: Optional[str]


@dataclass
class KeepAliveData:
    keepAlive: str


@dataclass
class KeepAliveMessage:
    id: str
    type: str
    data: KeepAliveData
    time: datetime
    dataContentType: str
    source: str
    traceParent: Optional[str]


@dataclass
class VehicleStatus:
    maxBatteryLevel: float
    batteryLevel: int
    range: int
    chargeLimit: int
    chargingStatus: str


@dataclass
class VehicleFeatures:
    charging: bool
    smartCharging: bool


@dataclass
class SmartChargingStatus:
    smartChargingStatus: str
    dailyDeadline: Optional[str]
    dailyDeadlineDateTime: Optional[str]
    isCharging: bool
    protectiveChargeLimit: int
    warning: Optional[str]


@dataclass
class Session:
    date: datetime
    location: Optional[str]
    sessionType: str
    energyInKwh: float
    cost: float
    savings: float


@dataclass
class Summary:
    energyInKwh: float
    chargingTimeInHours: int
    savings: float


@dataclass
class VehicleDetailsData:
    name: str
    id: str
    image: str
    vehicleStatus: VehicleStatus
    sessions: List[Session]
    vehicleFeatures: VehicleFeatures
    currentSession: Optional[str]
    summary: Optional[Summary]
    smartChargingStatus: SmartChargingStatus
    reliabilityLevel: str


@dataclass
class VehicleDetailsUpdatedMessage:
    id: str
    type: str
    data: VehicleDetailsData
    time: datetime
    dataContentType: str
    source: str
    traceParent: Optional[str]


@dataclass
class Weather:
    description: str
    main: str
    icon: str
    temperature: float


@dataclass
class SpotPriceData:
    time: str
    value: float
    rating: str


@dataclass
class DayData:
    lowestAt: str
    highestAt: str
    average: float
    data: List[SpotPriceData]


@dataclass
class SpotPrice:
    rating: str
    value: float
    unit: str
    time: str
    twoDays: DayData
    today: DayData
    tomorrow: Optional[DayData]


@dataclass
class Source:
    type: str
    value: float
    size: float
    unit: str


@dataclass
class Destination:
    type: str
    value: float
    size: float
    unit: str


@dataclass
class StatusRightNow:
    status: str
    sources: List[Source]
    destinations: List[Destination]


@dataclass
class Location:
    id: str
    name: str
    city: str
    weather: Optional[Weather]
    spotPrice: Optional[SpotPrice]
    solar: Optional[None]
    statusRightNow: Optional[StatusRightNow]
