from airtouch5py.packets.datapacket import Data


class ZoneName:
    zone_number: int
    zone_name: str


class ZoneNameData(Data):
    zone_names: list[ZoneName]
