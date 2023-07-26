import struct

from airtouch5py.packet_fields import MessageType
from airtouch5py.packets.ac_ability import AcAbilityData, AcAbilityRequestData
from airtouch5py.packets.ac_control import AcControlData, SetpointControl
from airtouch5py.packets.ac_error_information import (
    AcErrorInformationData,
    AcErrorInformationRequestData,
)
from airtouch5py.packets.ac_status import AcStatusData
from airtouch5py.packets.console_version import (
    ConsoleVersionData,
    ConsoleVersionRequestData,
)
from airtouch5py.packets.datapacket import Data, DataPacket
from airtouch5py.packets.zone_control import ZoneControlData, ZoneSettingValue
from airtouch5py.packets.zone_name import ZoneNameData, ZoneNameRequestData

from airtouch5py.packets.zone_status import ZoneStatusData

from crc import Calculator, Crc16

_calculator = Calculator(Crc16.MODBUS)  # type: ignore


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
        res += struct.pack(">H", len(packet_data))
        # Data
        res += packet_data

        # CRC16 check bytes
        res += struct.pack(">H", _calculator.checksum(res[4:]))

        # h. Redundant bytes in message
        # To prevent the message from containing the same data as header, a 00 is inserted after every three
        # consecutive 0x55s in the message. The inserted 00 is redundant bytes
        # ^^ In testing this actually doesn't happen. I named a zone UUUUUUU and it didn't insert any 00s

        return res

    def _message_type(self, data: Data) -> MessageType:
        match data:
            case ZoneControlData() | ZoneStatusData() | AcControlData() | AcStatusData():
                return MessageType.CONTROL_STATUS
            case AcAbilityRequestData() | AcAbilityData() | AcErrorInformationRequestData() | AcErrorInformationData() | ZoneNameRequestData() | ZoneNameData() | ConsoleVersionRequestData() | ConsoleVersionData():
                return MessageType.EXTENDED
            case _:
                raise Exception(f"Unknown message type for {data.__class__.__name__}")

    def _encode_data(self, data: Data) -> bytes:
        match data:
            case ZoneControlData():
                return self._encode_zone_control_data(data)
            case ZoneStatusData():
                return self._encode_zone_status_data(data)
            case AcControlData():
                return self._encode_ac_control_data(data)
            case AcStatusData():
                return self._encode_ac_status_data(data)
            case AcAbilityRequestData():
                return self._encode_ac_ability_request_data(data)
            case AcAbilityData():
                return self._encode_ac_ability_data(data)
            case AcErrorInformationRequestData():
                return self._encode_ac_error_information_request_data(data)
            case AcErrorInformationData():
                return self._encode_ac_error_information_data(data)
            case ZoneNameRequestData():
                return self._encode_zone_name_request_data(data)
            case ZoneNameData():
                return self._encode_zone_name_data(data)
            case ConsoleVersionRequestData():
                return self._encode_console_version_request_data(data)
            case ConsoleVersionData():
                return self._encode_console_version_data(data)
            case _:
                raise Exception(f"Unknown data type for {data.__class__.__name__}")

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
                ">B", (zone.zone_setting_value.value << 5) | (zone.power.value << 0)
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

    def _encode_zone_status_data(self, data: ZoneStatusData) -> bytes:
        # Sub message type 0x21
        # 0
        # no normal data (2 bytes)
        # each repeat data length, only if there is repeat data (2 bytes, 8)
        res = b"\x21\x00\x00\x00\x00"
        if len(data.zones) == 0:
            res += b"\x00"
        else:
            res += b"\x08"
        # repeat count (2 bytes)
        res += struct.pack(">H", len(data.zones))

        # pack the zone statuses
        for zone in data.zones:
            # Byte 1 Bit 8-7 Zone power state
            # Byte 1 Bit 6-1 Zone number
            res += struct.pack(
                ">B", (zone.zone_power_state.value << 6) | (zone.zone_number)
            )

            # Byte 2 Bit 8 control method (temperature = 1, percentage = 0)
            # Byte 2 Bit 7-1 Open percentage
            res += struct.pack(
                ">B", (zone.control_method.value << 7) | int(zone.open_percentage * 100)
            )

            # Byte 3 Set point setpoint=(value+100)/10, 0xFF invalid (None)
            if zone.set_point is None:
                res += b"\xFF"
            else:
                res += struct.pack(">B", int(zone.set_point * 10 - 100))

            # Byte 4 Bit 8 has sensor
            # Byte 4 Bit 7-1 NOT USED
            res += struct.pack(">B", (zone.has_sensor << 7))

            # Byte 5-6 Temperature Temperature > 150 invalid (None)
            if zone.temperature is None:
                res += b"\x07\xFF"  # The sample packs this
            else:
                res += struct.pack(">H", int(zone.temperature * 10 + 500))

            # Byte 7 Bit 8-3 NOT USED
            # Byte 7 Bit 2 Spill active
            # Byte 7 Bit 1 Low battery
            res += struct.pack(
                ">B", (zone.spill_active << 1) | (zone.is_low_battery << 0)
            )

            # Byte 8 NOT USED
            res += b"\x00"

        return res

    def _encode_ac_control_data(self, data: AcControlData) -> bytes:
        # Sub message type 0x22
        # 0
        # no normal data (2 bytes)
        # each repeat data length (2 bytes, 4)
        res = b"\x22\x00\x00\x00\x00\x04"
        # repeat count (2 bytes)
        res += struct.pack(">H", len(data.ac_control))

        # pack the ac controls
        for ac in data.ac_control:
            # Byte 1 Bit 8-5 Power setting
            # Byte 1 Bit 4-1 AC number
            res += struct.pack(">B", (ac.power_setting.value << 4) | (ac.ac_number))

            # Byte 2 Bit 8-5 AC mode
            # Byte 2 Bit 4-1 AC fan speed
            res += struct.pack(">B", (ac.ac_mode.value << 4) | (ac.ac_fan_speed.value))

            # Byte 3 Setpoint control
            res += struct.pack(">B", ac.setpoint_control.value)

            # Byte 4 Setpoint value (Available when byte 3 is Change setpoint)
            match ac.setpoint_control:
                case SetpointControl.CHANGE_SETPOINT:
                    res += struct.pack(">B", int(ac.setpoint * 10 - 100))
                case SetpointControl.KEEP_SETPOINT_VALUE | SetpointControl.INVALIDATE_DATA:
                    res += b"\xFF"
                case _:
                    raise Exception(
                        f"Unsupported setpoint control {ac.setpoint_control}"
                    )

        return res

    def _encode_ac_status_data(self, data: AcStatusData) -> bytes:
        # Sub message type 0x23
        # 0
        # no normal data (2 bytes)
        # each repeat data length, only if there is repeat data (2 bytes, 10)
        res = b"\x23\x00\x00\x00\x00"
        if len(data.ac_status) == 0:
            res += b"\x00"
        else:
            res += b"\x0A"
        # repeat count (2 bytes)
        res += struct.pack(">H", len(data.ac_status))

        # pack the ac statuses
        for ac in data.ac_status:
            # Byte 1 Bit 8-5 AC power state
            # Byte 1 Bit 4-1 AC number
            res += struct.pack(">B", (ac.ac_power_state.value << 4) | (ac.ac_number))

            # Byte 2 Bit 8-5 AC mode
            # Byte 2 Bit 4-1 AC fan speed
            res += struct.pack(">B", (ac.ac_mode.value << 4) | (ac.ac_fan_speed.value))

            # Byte 3 Setpoint (0xFF if Not Available)
            if ac.ac_setpoint is None:
                res += b"\xFF"
            else:
                res += struct.pack(">B", int(ac.ac_setpoint * 10 - 100))

            # Byte 4 Bit 8-5 NOT USED (Packed as C in the sample)
            # Byte 4 Bit 4 Turbo active
            # Byte 4 Bit 3 Bypass active
            # Byte 4 Bit 2 Spill active
            # Byte 4 Bit 1 Timer set
            res += struct.pack(
                ">B",
                0xC0
                | ac.turbo_active << 3
                | ac.bypass_active << 2
                | ac.spill_active << 1
                | ac.timer_set << 0,
            )

            # Byte 5-6 Temperature (0x07FF if Not Available)
            if ac.temperature is None:
                res += b"\x07\xFF"
            else:
                res += struct.pack(">H", int(ac.temperature * 10 + 500))

            # Byte 7-8 Error code
            res += struct.pack(">H", ac.error_code)

            # Byte 9-10 NOT USED (Sample packs 8000)
            res += b"\x80\x00"

        return res

    def _encode_ac_ability_request_data(self, data: AcAbilityRequestData) -> bytes:
        # Sub message type 0xFF11
        res = b"\xFF\x11"

        if data.ac_number is not None:
            res += struct.pack(">B", data.ac_number)

        return res

    def _encode_ac_ability_data(self, data: AcAbilityData) -> bytes:
        # Sub message type 0xFF11
        res = b"\xFF\x11"

        # Pack each ac
        for ac in data.ac_ability:
            # Byte 3 AC number
            res += struct.pack(">B", ac.ac_number)

            # Byte 4 Following data length (24)
            res += b"\x18"

            # Byte 5-20 AC Name (Null padded)
            res += ac.ac_name.encode("ascii").ljust(16, b"\x00")

            # Byte 21 start zone number
            res += struct.pack(">B", ac.start_zone_number)

            # Byte 22 zone count
            res += struct.pack(">B", ac.zone_count)

            # Byte 23 Bit 8-6 NOT USED
            # Byte 23 Bit 5 Cool mode supported
            # Byte 23 Bit 4 Fan mode supported
            # Byte 23 Bit 3 Dry mode supported
            # Byte 23 Bit 2 Heat mode supported
            # Byte 23 Bit 1 Auto mode supported
            res += struct.pack(
                ">B",
                0x00
                | ac.supports_mode_cool << 4
                | ac.supports_mode_fan << 3
                | ac.supports_mode_dry << 2
                | ac.supports_mode_heat << 1
                | ac.supports_mode_auto << 0,
            )

            # Byte 24 Bit 8 Supports intelligent auto fan speed
            # Byte 24 Bit 7 Supports turbo fan speed
            # Byte 24 Bit 6 Supports powerful fan speed
            # Byte 24 Bit 5 Supports high fan speed
            # Byte 24 Bit 4 Supports medium fan speed
            # Byte 24 Bit 3 Supports low fan speed
            # Byte 24 Bit 2 Supports quiet fan speed
            # Byte 24 Bit 1 Supports auto fan speed
            res += struct.pack(
                ">B",
                0x00
                | ac.supports_fan_speed_intelligent_auto << 7
                | ac.supports_fan_speed_turbo << 6
                | ac.supports_fan_speed_powerful << 5
                | ac.supports_fan_speed_high << 4
                | ac.supports_fan_speed_medium << 3
                | ac.supports_fan_speed_low << 2
                | ac.supports_fan_speed_quiet << 1
                | ac.supports_fan_speed_auto << 0,
            )

            # Byte 25 Min cool set point
            res += struct.pack(">B", ac.min_cool_set_point)
            # Byte 26 Max cool set point
            res += struct.pack(">B", ac.max_cool_set_point)
            # Byte 27 Min heat set point
            res += struct.pack(">B", ac.min_heat_set_point)
            # Byte 28 Max heat set point
            res += struct.pack(">B", ac.max_heat_set_point)

        return res

    def _encode_ac_error_information_request_data(
        self, data: AcErrorInformationRequestData
    ) -> bytes:
        # Sub message type 0xFF10
        res = b"\xFF\x10"

        if data.ac_number is not None:
            res += struct.pack(">B", data.ac_number)

        return res

    def _encode_ac_error_information_data(self, data: AcErrorInformationData) -> bytes:
        # Sub message type 0xFF10
        res = b"\xFF\x10"

        # Byte 3 AC number
        res += struct.pack(">B", data.ac_number)
        # Byte 4 Error info length (0 if no error)
        res += struct.pack(">B", len(data.error_info))
        # Byte 5.. Error info (no bytes if no error, no null at end)
        res += data.error_info.encode("ascii")

        return res

    def _encode_zone_name_request_data(self, data: ZoneNameRequestData) -> bytes:
        # Sub message type 0xFF13
        res = b"\xFF\x13"

        if data.zone_number is not None:
            res += struct.pack(">B", data.zone_number)

        return res

    def _encode_zone_name_data(self, data: ZoneNameData) -> bytes:
        # Sub message type 0xFF13
        res = b"\xFF\x13"

        # Pack each zone
        for zone in data.zone_names:
            # Byte 3 Zone number
            res += struct.pack(">B", zone.zone_number)

            # Byte 4 Name length
            res += struct.pack(">B", len(zone.zone_name))

            # Byte 5.. Zone name (no null at end)
            res += zone.zone_name.encode("ascii")

        return res

    def _encode_console_version_request_data(
        self, data: ConsoleVersionRequestData
    ) -> bytes:
        # Sub message type 0xFF30
        res = b"\xFF\x30"

        return res

    def _encode_console_version_data(self, data: ConsoleVersionData) -> bytes:
        # Sub message type 0xFF30
        res = b"\xFF\x30"

        # Byte 3 Update sign (0 - latest, Other - new version available)
        res += struct.pack(">B", data.has_update)

        # Byte 4 Version length
        res += struct.pack(">B", len(data.version))

        # Byte 5.. Version (no null at end)
        res += data.version.encode("ascii")

        return res
