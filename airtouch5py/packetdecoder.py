import struct
from enum import Enum

from airtouch5py.packets.datapacket import Data, DataPacket
from airtouch5py.packets.zone_control import (
    ZoneControlData,
    ZoneControlZone,
    ZoneSettingPower,
    ZoneSettingValue,
)
from bitarray import bitarray
from bitarray.util import ba2int


class PacketType(Enum):
    # Control command and status message
    CONTROL_STATUS = 0xC0
    EXTENDED = 0x1F


class ControlStatusSubType(Enum):
    ZONE_CONTROL = 0x20
    ZONE_STATUS = 0x21
    AC_CONTROL = 0x22
    AC_STATUS = 0x23


class ExtendedMessageSubType(Enum):
    AC_ABILITY = 0xFF11
    AC_ERROR_INFORMATION = 0xFF10
    ZONE_NAME = 0xFF13
    CONSOLE_VERSION = 0xFF30


class PacketDecoder:
    """
    Decode packets from the AirTouch 5 protocol.
    Assumes that they have already been validated (CRC, data length)
    """

    # https://stackoverflow.com/questions/43634618/how-do-i-test-if-int-value-exists-in-python-enum-without-using-try-catch
    _set_ZoneSettingValue = set(item.value for item in ZoneSettingValue)
    _set_ZoneSettingPower = set(item.value for item in ZoneSettingPower)

    def decode(self, buffer: bytes) -> DataPacket:
        # Header (4 bytes)
        # Address (2 bytes)
        # Message ID (1 byte)
        # Message type (1 byte)
        # Data length (2 bytes)
        # Data (variable)
        # CRC (2 bytes)

        # if len(bytes) < 4 + 2 + 1 + 1 + 2 + 2:
        #    raise ValueError("Packet is too short")

        # TODO: Could do these all in one unpack call?
        address: int = struct.unpack(">H", buffer[4:6])[0]
        message_id: int = struct.unpack(">B", buffer[6:7])[0]
        message_type: int = struct.unpack(">B", buffer[7:8])[0]
        data_length: int = struct.unpack(">H", buffer[8:10])[0]
        data_bytes: bytes = buffer[10 : data_length + 10]

        data: Data
        match message_type:
            case PacketType.CONTROL_STATUS.value:
                data = self.decode_control_status(data_bytes)
            case PacketType.EXTENDED.value:
                data = self.decode_extended(data_bytes)
            case _:
                raise ValueError(f"Unknown message type: {hex(message_type)}")

        return DataPacket(address, message_id, data)

    def decode_control_status(self, bytes: bytes) -> Data:
        # Sub message type (1 byte)
        # Keep 0 (1 byte)
        # Normal data length (2 bytes)
        # Each repeat data length (2 bytes)
        # Repeat data count (2 bytes)

        sub_message_type = struct.unpack(">B", bytes[0:1])[0]
        normal_data_length = struct.unpack(">H", bytes[2:4])[0]
        repeat_data_length = struct.unpack(">H", bytes[4:6])[0]
        repeat_data_count = struct.unpack(">H", bytes[6:8])[0]

        # Should now have normal_data_length of data, then repeat length * data_count
        if (
            len(bytes) - 8
            != normal_data_length + repeat_data_length * repeat_data_count
        ):
            raise ValueError("Data length does not match")

        match sub_message_type:
            case ControlStatusSubType.ZONE_CONTROL.value:
                if normal_data_length != 0:
                    raise ValueError("Zone control message should not have normal data")
                if repeat_data_length != 4:
                    raise ValueError(
                        "Zone control message should have 4 byte repeat data"
                    )
                return self.decode_zone_control(bytes[8:], repeat_data_count)
            case ControlStatusSubType.ZONE_STATUS.value:
                if normal_data_length != 0:
                    raise ValueError("Zone status message should not have normal data")
                if repeat_data_length != 8:
                    raise ValueError(
                        "Zone status message should have 8 byte repeat data"
                    )
                return self.decode_zone_status(bytes[8:], repeat_data_count)
            case ControlStatusSubType.AC_CONTROL.value:
                if normal_data_length != 0:
                    raise ValueError("AC control message should not have normal data")
                if repeat_data_length != 4:
                    raise ValueError(
                        "AC control message should have 4 byte repeat data"
                    )
                return self.decode_ac_control(bytes[8:], repeat_data_count)
            case ControlStatusSubType.AC_STATUS.value:
                if normal_data_length != 0:
                    raise ValueError("AC status message should not have normal data")
                if repeat_data_length != 10:
                    raise ValueError(
                        "AC status message should have 10 byte repeat data"
                    )
                return self.decode_ac_status(bytes[8:], repeat_data_count)
            case _:
                raise ValueError(f"Unknown sub message type: {hex(sub_message_type)}")

    def decode_zone_control(self, bytes: bytes, repeat_data_count: int) -> Data:
        zones: list[ZoneControlZone] = []
        bits = bitarray(endian="big")

        for i in range(0, repeat_data_count):
            bits.frombytes(bytes[i * 4 : i * 4 + 4])
            # Byte 1 Bit 6-1 Zone number
            zone_number = ba2int(bits[2:8])
            # Byte 2 Bit 8-6 Zone setting value (Can be invalid -> KEEP_SETTING_VALUE)
            zone_setting_value = ba2int(bits[8 + 0 : 8 + 3])
            if zone_setting_value in self._set_ZoneSettingValue:
                zone_setting_value = ZoneSettingValue(zone_setting_value)
            else:
                zone_setting_value = ZoneSettingValue.KEEP_SETTING_VALUE
            # Byte 2 bit 3-1 Power
            power = ba2int(bits[8 + 5 : 8 + 8])
            if power in self._set_ZoneSettingPower:
                power = ZoneSettingPower(power)
            else:
                power = ZoneSettingPower.KEEP_POWER_STATE
            # Byte 3 Value to set
            value_to_set = ba2int(bits[16 : 16 + 8])

            if zone_setting_value == ZoneSettingValue.SET_OPEN_PERCENTAGE:
                value_to_set = value_to_set / 100
            elif zone_setting_value == ZoneSettingValue.SET_TARGET_SETPOINT:
                value_to_set = (value_to_set + 100) / 10

            zones.append(
                ZoneControlZone(zone_number, zone_setting_value, power, value_to_set)
            )
        return ZoneControlData(zones)

    def decode_zone_status(self, bytes: bytes, repeat_data_count: int) -> Data:
        raise NotImplementedError()

    def decode_ac_control(self, bytes: bytes, repeat_data_count: int) -> Data:
        raise NotImplementedError()

    def decode_ac_status(self, bytes: bytes, repeat_data_count: int) -> Data:
        raise NotImplementedError()

    def decode_extended(self, bytes: bytes) -> Data:
        # Sub message type (2 bytes)
        sub_message_type = struct.unpack(">H", bytes[0:2])[0]
        message_bytes = bytes[2:]

        match sub_message_type:
            case ExtendedMessageSubType.AC_ABILITY.value:
                return self.decode_ac_ability(message_bytes)
            case ExtendedMessageSubType.AC_ERROR_INFORMATION.value:
                return self.decode_ac_error_information(message_bytes)
            case ExtendedMessageSubType.ZONE_NAME.value:
                return self.decode_zone_name(message_bytes)
            case ExtendedMessageSubType.CONSOLE_VERSION.value:
                return self.decode_console_version(message_bytes)
            case _:
                raise ValueError(f"Unknown sub message type: {hex(sub_message_type)}")

    def decode_ac_ability(self, bytes: bytes) -> Data:
        raise NotImplementedError()

    def decode_ac_error_information(self, bytes: bytes) -> Data:
        raise NotImplementedError()

    def decode_zone_name(self, bytes: bytes) -> Data:
        raise NotImplementedError()

    def decode_console_version(self, bytes: bytes) -> Data:
        raise NotImplementedError()
