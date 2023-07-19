from enum import Enum


class Data:
    pass

class ZoneSettingValue(Enum):
    ValueDecrease = 0b010
    ValueIncrease = 0b011
    SetOpenPercentage = 0b100
    SetTargetSetpoint = 0b101
    #Other: Keep setting value

class ZoneSettingPower(Enum):
    ChangeOnOffState = 0b001
    SetToOff = 0b010
    SetToOn = 0b011
    SetToTurbo = 0b101
    #Other: Keep power state

class ZoneControlZone:
    zone_number: int
    zone_setting_value: ZoneSettingValue
    power: ZoneSettingPower
    value_to_set: float

"""
Zone control messages are to control all zones. Each message to AirTouch is to control one or more specific zones.
AirTouch will respond a message with sub type 0x21. (Zone status message)
"""
class ZoneControlData(Data):
    zones: list[ZoneControlZone]

class ZonePowerState(Enum):
    Off = 0b00
    On = 0b01
    Turbo = 0b11

class ControlMethod(Enum):
    TemperatureControl = 1
    PercentageControl = 0

class ZoneStatusZone:
    zone_power_state: ZonePowerState
    zone_number: int
    control_method: ControlMethod
    open_percentage: int
    set_point: float #0xFF invalid
    has_sensor: bool
    temperature: float #Temperature > 150 invalid
    spill_active: bool
    is_low_battery: bool

"""
Send this message to AirTouch without any sub data (data length: 0x00 0x08, repeat count: 0x00, repeat length: 0x00) to request zone status from AirTouch.

Note: AirTouch will send a zone status message automatically when zone status is changed.
"""
class ZoneStatusData(Data):
    zones: list[ZoneStatusZone]

class SetPowerSetting(Enum):
    ChangeOnOffStatus = 0b0001 #Does this mean toggle?
    SetToOff = 0b0010
    SetToOn = 0b0011
    SetToAway = 0b0100
    SetToSleep = 0b0101
    #Other: Keep power setting

class SetAcMode(Enum):
    SetToAuto = 0b0000
    SetToHeat = 0b0001
    SetToDry = 0b0010
    SetToFan = 0b0011
    SetToCool = 0b0100
    #Other: keep mode setting

class SetAcFanSpeed(Enum):
    SetToAuto = 0b0000
    SetToQuiet = 0b0001 #"Quite" in the docs
    SetToLow = 0b0010
    SetToMedium = 0b0011
    SetToHigh = 0b0100
    SetToPowerful = 0b0101
    SetToTurbo = 0b0110
    SetToIntelligentAuto = 0b1000
    #Other: keep fan speed setting

class SetpointControl(Enum):
    ChangeSetpoint = 0x40
    KeepSetpointValue = 0x00
    #Other: Invalidate data (????)

class AcControl:
    power_setting: SetPowerSetting
    ac_number: int
    ac_mode: SetAcMode
    ac_fan_speed: SetAcFanSpeed
    setpoint_control: SetpointControl
    setpoint: float

"""
AC control messages are to control all ACs. Each message to AirTouch is to control one or more specific ACs.
AirTouch will respond a message with sub type 0x23. (AC status message)
"""
class AcControlData(Data):
    ac_control: list[AcControl]

class AcPowerState(Enum):
    Off = 0b0000
    On = 0b0001
    AwayOff = 0b0010
    AwayOn = 0b0011
    Sleep = 0b0101
    #Other: Not available

class AcMode(Enum):
    Auto = 0b0000
    Heat = 0b0001
    Dry = 0b0010
    Fan = 0b0011
    Cool = 0b0100
    AutoHeat = 0b1000
    AutoCool = 0b1001
    #Other: Not available

class AcFanSpeed(Enum):
    Auto = 0b0000
    Quiet = 0b0001
    Low = 0b0010
    Medium = 0b0011
    High = 0b0100
    Powerful = 0b0101
    Turbo = 0b0110
    IntelligentAuto1 = 0b1001
    IntelligentAuto2 = 0b1010
    IntelligentAuto3 = 0b1011
    IntelligentAuto4 = 0b1100
    IntelligentAuto5 = 0b1101
    IntelligentAuto6 = 0b1110
    #Other: Not available

class AcStatus:
    ac_power_state: AcPowerState
    ac_number: int
    ac_mode: AcMode
    ac_fan_speed: AcFanSpeed
    ac_setpoint: float
    turbo_active: bool
    bypass_active: bool
    spill_active: bool
    timer_set: bool
    temperature: float
    error_code: int

class AcStatusData(Data):
    ac_status: list[AcStatus]

class AcAbility:
    ac_number: int
    ac_name: str
    start_zone_number: int
    zone_count: int

    supports_mode_cool: bool
    supports_mode_fan: bool
    supports_mode_dry: bool
    supports_mode_heat: bool
    supports_mode_auto: bool
    
    supports_fan_speed_intelligent_auto: bool
    supports_fan_speed_turbo: bool
    supports_fan_speed_powerful: bool
    supports_fan_speed_high: bool
    supports_fan_speed_medium: bool
    supports_fan_speed_low: bool
    supports_fan_speed_quiet: bool #quite in docs
    supports_fan_speed_auto: bool

    #TODO: The docs are wrong for these, need to figure out what the field order is
    min_cool_set_point: float
    max_cool_set_point: float
    min_heat_set_point: float
    max_heat_set_point: float

class AcAbilityPacket(Data):
    ac_ability: list[AcAbility]

class AcErrorInformationData(Data):
    ac_number: int
    error_info: str

class ZoneName:
    zone_number: int
    zone_name: str

class ZoneNameData(Data):
    zone_names: list[ZoneName]

class ConsoleVersionData(Data):
    has_update: bool
    version: str

class DataPacket:
    address: int
    message_id: int

    data: Data
