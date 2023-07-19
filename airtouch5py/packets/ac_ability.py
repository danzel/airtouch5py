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

    # TODO: The docs are wrong for these, need to figure out what the field order is
    min_cool_set_point: float
    max_cool_set_point: float
    min_heat_set_point: float
    max_heat_set_point: float


class AcAbilityPacket(Data):
    ac_ability: list[AcAbility]
