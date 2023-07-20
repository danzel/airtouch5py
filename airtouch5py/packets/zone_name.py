from airtouch5py.packets.datapacket import Data


class ZoneName:
    zone_number: int
    zone_name: str

    def __init__(self, zone_number: int, zone_name: str):
        self.zone_number = zone_number
        self.zone_name = zone_name


class ZoneNameRequestData(Data):
    zone_number: int | None  # None for all

    def __init__(self, zone_number: int | None):
        self.zone_number = zone_number


class ZoneNameData(Data):
    zone_names: list[ZoneName]

    def __init__(self, zone_names: list[ZoneName]):
        self.zone_names = zone_names
