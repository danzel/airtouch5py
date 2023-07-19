from enum import Enum

from airtouch5py.packets.datapacket import Data


class ZoneSettingValue(Enum):
    KEEP_SETTING_VALUE = (
        0b000  # This should be used for any value that is not explicitly defined
    )
    VALUE_DECREASE = 0b010
    VALUE_INCREASE = 0b011
    SET_OPEN_PERCENTAGE = 0b100
    SET_TARGET_SETPOINT = 0b101
    # Other: Keep setting value


class ZoneSettingPower(Enum):
    KEEP_POWER_STATE = (
        0b000  # This should be used for any value that is not explicitly defined
    )
    CHANGE_ON_OFF_STATE = 0b001
    SET_TO_OFF = 0b010
    SET_TO_ON = 0b011
    SET_TO_TURBO = 0b101
    # Other: Keep power state


class ZoneControlZone:
    zone_number: int
    zone_setting_value: ZoneSettingValue
    power: ZoneSettingPower
    value_to_set: float

    def __init__(
        self,
        zone_number: int,
        zone_setting_value: ZoneSettingValue,
        power: ZoneSettingPower,
        value_to_set: float,
    ):
        self.zone_number = zone_number
        self.zone_setting_value = zone_setting_value
        self.power = power
        self.value_to_set = value_to_set


class ZoneControlData(Data):
    """
    Zone control messages are to control all zones. Each message to AirTouch is to control one or more specific zones.
    AirTouch will respond a message with sub type 0x21. (Zone status message)
    """

    zones: list[ZoneControlZone]

    def __init__(self, zones: list[ZoneControlZone]):
        self.zones = zones
