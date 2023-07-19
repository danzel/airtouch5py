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
    open_percentage: int
    set_point: float  # 0xFF invalid
    has_sensor: bool
    temperature: float  # Temperature > 150 invalid
    spill_active: bool
    is_low_battery: bool


class ZoneStatusData(Data):
    """
    Send this message to AirTouch without any sub data (data length: 0x00 0x08, repeat count: 0x00, repeat length: 0x00) to request zone status from AirTouch.
    Note: AirTouch will send a zone status message automatically when zone status is changed.
    """

    zones: list[ZoneStatusZone]
