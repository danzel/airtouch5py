from enum import Enum

from airtouch5py.packets.datapacket import Data


class AcPowerState(Enum):
    NOT_AVAILABLE = (
        0b1111  # This should be used for any value that is not explicitly defined
    )
    OFF = 0b0000
    ON = 0b0001
    AWAY_OFF = 0b0010
    AWAY_ON = 0b0011
    SLEEP = 0b0101
    # Other: Not available


class AcMode(Enum):
    NOT_AVAILABLE = (
        0b1111  # This should be used for any value that is not explicitly defined
    )
    AUTO = 0b0000
    HEAT = 0b0001
    DRY = 0b0010
    FAN = 0b0011
    COOL = 0b0100
    AUTO_HEAT = 0b1000
    AUTO_COOL = 0b1001
    # Other: Not available


class AcFanSpeed(Enum):
    NOT_AVAILABLE = (
        0b1111  # This should be used for any value that is not explicitly defined
    )
    AUTO = 0b0000
    QUIET = 0b0001
    LOW = 0b0010
    MEDIUM = 0b0011
    HIGH = 0b0100
    POWERFUL = 0b0101
    TURBO = 0b0110
    INTELLIGENT_AUTO_1 = 0b1001
    INTELLIGENT_AUTO_2 = 0b1010
    INTELLIGENT_AUTO_3 = 0b1011
    INTELLIGENT_AUTO_4 = 0b1100
    INTELLIGENT_AUTO_5 = 0b1101
    INTELLIGENT_AUTO_6 = 0b1110
    # Other: Not available


class AcStatus:
    ac_power_state: AcPowerState
    ac_number: int
    ac_mode: AcMode
    ac_fan_speed: AcFanSpeed
    ac_setpoint: float | None  # Other: Not available
    turbo_active: bool
    bypass_active: bool
    spill_active: bool
    timer_set: bool
    temperature: float | None  # Other: Not available
    error_code: int

    def __init__(
        self,
        ac_power_state: AcPowerState,
        ac_number: int,
        ac_mode: AcMode,
        ac_fan_speed: AcFanSpeed,
        ac_setpoint: float | None,
        turbo_active: bool,
        bypass_active: bool,
        spill_active: bool,
        timer_set: bool,
        temperature: float | None,
        error_code: int,
    ):
        self.ac_power_state = ac_power_state
        self.ac_number = ac_number
        self.ac_mode = ac_mode
        self.ac_fan_speed = ac_fan_speed
        self.ac_setpoint = ac_setpoint
        self.turbo_active = turbo_active
        self.bypass_active = bypass_active
        self.spill_active = spill_active
        self.timer_set = timer_set
        self.temperature = temperature
        self.error_code = error_code


class AcStatusData(Data):
    ac_status: list[AcStatus]

    def __init__(self, ac_status: list[AcStatus]):
        self.ac_status = ac_status
