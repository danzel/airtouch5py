from airtouch5py.packets.datapacket import Data


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
    supports_fan_speed_quiet: bool  # quite in docs
    supports_fan_speed_auto: bool

    # The docs are wrong for these (they are all cool)
    min_cool_set_point: int
    max_cool_set_point: int
    min_heat_set_point: int
    max_heat_set_point: int

    def __init__(
        self,
        ac_number: int,
        ac_name: str,
        start_zone_number: int,
        zone_count: int,
        supports_mode_cool: bool,
        supports_mode_fan: bool,
        supports_mode_dry: bool,
        supports_mode_heat: bool,
        supports_mode_auto: bool,
        supports_fan_speed_intelligent_auto: bool,
        supports_fan_speed_turbo: bool,
        supports_fan_speed_powerful: bool,
        supports_fan_speed_high: bool,
        supports_fan_speed_medium: bool,
        supports_fan_speed_low: bool,
        supports_fan_speed_quiet: bool,
        supports_fan_speed_auto: bool,
        min_cool_set_point: int,
        max_cool_set_point: int,
        min_heat_set_point: int,
        max_heat_set_point: int,
    ):
        self.ac_number = ac_number
        self.ac_name = ac_name
        self.start_zone_number = start_zone_number
        self.zone_count = zone_count
        self.supports_mode_cool = supports_mode_cool
        self.supports_mode_fan = supports_mode_fan
        self.supports_mode_dry = supports_mode_dry
        self.supports_mode_heat = supports_mode_heat
        self.supports_mode_auto = supports_mode_auto
        self.supports_fan_speed_intelligent_auto = supports_fan_speed_intelligent_auto
        self.supports_fan_speed_turbo = supports_fan_speed_turbo
        self.supports_fan_speed_powerful = supports_fan_speed_powerful
        self.supports_fan_speed_high = supports_fan_speed_high
        self.supports_fan_speed_medium = supports_fan_speed_medium
        self.supports_fan_speed_low = supports_fan_speed_low
        self.supports_fan_speed_quiet = supports_fan_speed_quiet
        self.supports_fan_speed_auto = supports_fan_speed_auto
        self.min_cool_set_point = min_cool_set_point
        self.max_cool_set_point = max_cool_set_point
        self.min_heat_set_point = min_heat_set_point
        self.max_heat_set_point = max_heat_set_point


class AcAbilityData(Data):
    ac_ability: list[AcAbility]

    def __init__(self, ac_ability: list[AcAbility]):
        self.ac_ability = ac_ability


class AcAbilityRequestData(Data):
    ac_number: int | None  # None to request the ability of all ACs

    def __init__(self, ac_number: int | None):
        self.ac_number = ac_number
