import struct

from airtouch5py.packet_fields import MessageType
from airtouch5py.packets.datapacket import Data, DataPacket
from airtouch5py.packets.zone_control import ZoneControlData, ZoneSettingValue


class PacketEncoder:
    header = b"\x55\x55\x55\xAA"

    def encode(self, packet: DataPacket) -> bytes:
        # Header is always 0x55 0x55 0x55 0xAA
        res = self.header
        # Address, Message id
        res += struct.pack(">HB", packet.address, packet.message_id)
        # Message type
        res += struct.pack(">B", self._message_type(packet.data).value)

        # Data length (2bytes)
        packet_data = self._encode_data(packet.data)
        print(packet_data)
        res += struct.pack(">H", len(packet_data))
        # Data
        res += packet_data

        # CRC16 check bytes

        return res

    def _message_type(self, data: Data) -> MessageType:
        match data:
            case ZoneControlData():
                return MessageType.CONTROL_STATUS
            case _:
                raise Exception(f"Unknown message type for {data.__class__.__name__}")

    def _encode_data(self, data: Data) -> bytes:
        match data:
            case ZoneControlData():
                return self._encode_zone_control_data(data)
            case _:
                raise Exception("Unknown data type")

    def _encode_zone_control_data(self, data: ZoneControlData) -> bytes:
        # Sub message type 0x20
        # 0
        # no normal data (2 bytes)
        # each repeat data length (2 bytes, 4)
        res = b"\x20\x00\x00\x00\x00\x04"
        # repeat count (2 bytes)
        res += struct.pack(">H", len(data.zones))

        # pack the zones
        for zone in data.zones:
            # Byte 1 Bit 8-7 Keep 0
            # Byte 1 Bit 6-1 Zone number
            res += struct.pack(">B", zone.zone_number)

            # Byte 2 Bit 8-7 Zone setting value
            # Byte 2 Bit 5-4 Keep 0
            # Byte 2 Bit 3-1 Power
            res += struct.pack(
                ">B", (zone.zone_setting_value.value << 6) | (zone.power.value << 0)
            )

            # Byte 3 Value to Set
            if zone.zone_setting_value == ZoneSettingValue.SET_OPEN_PERCENTAGE:
                res += struct.pack(">B", int(zone.value_to_set * 100))
            elif zone.zone_setting_value == ZoneSettingValue.SET_TARGET_SETPOINT:
                res += struct.pack(">B", int(zone.value_to_set * 10 - 100))
            elif zone.zone_setting_value == ZoneSettingValue.KEEP_SETTING_VALUE:
                res += b"\xFF"
            else:
                raise Exception(f"Unknown zone setting value {zone.zone_setting_value}")

            # Byte 4 Keep 0
            res += b"\x00"

        return res
