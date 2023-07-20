from enum import Enum

from airtouch5py.packets.datapacket import Data


class ZonePowerState(Enum):
    OFF = 0b00
    ON = 0b01
    TURBO = 0b11


class ControlMethod(Enum):
    TEMPERATURE_CONTROL = 1
    PERCENTAGE_CONTROL = 0


class ZoneStatusZone:
    zone_power_state: ZonePowerState
    zone_number: int
    control_method: ControlMethod
    open_percentage: float  # 0.0 - 1.0
    set_point: float | None  # 0xFF invalid (None)
    has_sensor: bool
    temperature: float | None  # Temperature > 150 invalid (None)
    spill_active: bool
    is_low_battery: bool

    def __init__(
        self,
        zone_power_state: ZonePowerState,
        zone_number: int,
        control_method: ControlMethod,
        open_percentage: float,
        set_point: float | None,
        has_sensor: bool,
        temperature: float | None,
        spill_active: bool,
        is_low_battery: bool,
    ):
        self.zone_power_state = zone_power_state
        self.zone_number = zone_number
        self.control_method = control_method
        self.open_percentage = open_percentage
        self.set_point = set_point
        self.has_sensor = has_sensor
        self.temperature = temperature
        self.spill_active = spill_active
        self.is_low_battery = is_low_battery


class ZoneStatusData(Data):
    """
    Send this message to AirTouch without any sub data (data length: 0x00 0x08, repeat count: 0x00, repeat length: 0x00) to request zone status from AirTouch.
    Note: AirTouch will send a zone status message automatically when zone status is changed.
    """

    zones: list[ZoneStatusZone]

    def __init__(self, zones: list[ZoneStatusZone]):
        self.zones = zones
