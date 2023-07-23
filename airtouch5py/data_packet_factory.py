from airtouch5py.packets.ac_ability import AcAbilityRequestData
from airtouch5py.packets.ac_control import AcControl, AcControlData
from airtouch5py.packets.ac_error_information import AcErrorInformationRequestData
from airtouch5py.packets.ac_status import AcStatusData
from airtouch5py.packets.console_version import ConsoleVersionRequestData
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_control import ZoneControlData, ZoneControlZone
from airtouch5py.packets.zone_name import ZoneNameRequestData
from airtouch5py.packets.zone_status import ZoneStatusData

ADDRESS = 0x80B0
EXTENDED_ADDRESS = 0x90B0


class DataPacketFactory:
    _id: int

    def __init__(self):
        self._id = 0x01

    def zone_control(self, zones: list[ZoneControlZone]) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(ADDRESS, self._id, ZoneControlData(zones))

    def zone_status_request(self) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(ADDRESS, self._id, ZoneStatusData([]))

    def ac_control(self, ac: list[AcControl]) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(ADDRESS, self._id, AcControlData(ac))

    def ac_status_request(self) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(ADDRESS, self._id, AcStatusData([]))

    def ac_ability_request(self, ac_number: int | None = None) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(EXTENDED_ADDRESS, self._id, AcAbilityRequestData(ac_number))

    def ac_error_information_request(self, ac_number: int) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(
            EXTENDED_ADDRESS, self._id, AcErrorInformationRequestData(ac_number)
        )

    def zone_name_request(self, zone_number: int | None = None) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(EXTENDED_ADDRESS, self._id, ZoneNameRequestData(zone_number))

    def console_version_request(self) -> DataPacket:
        self._id = self._id + 1 % 256
        return DataPacket(EXTENDED_ADDRESS, self._id, ConsoleVersionRequestData())
