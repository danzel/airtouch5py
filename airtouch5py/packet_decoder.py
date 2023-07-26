import struct

from airtouch5py.packet_fields import (
    ControlStatusSubType,
    ExtendedMessageSubType,
    MessageType,
)

from airtouch5py.packets.ac_ability import (
    AcAbility,
    AcAbilityData,
    AcAbilityRequestData,
)

from airtouch5py.packets.ac_control import (
    AcControl,
    AcControlData,
    SetAcFanSpeed,
    SetAcMode,
    SetpointControl,
    SetPowerSetting,
)
from airtouch5py.packets.ac_error_information import (
    AcErrorInformationData,
    AcErrorInformationRequestData,
)
from airtouch5py.packets.ac_status import (
    AcFanSpeed,
    AcMode,
    AcPowerState,
    AcStatus,
    AcStatusData,
)
from airtouch5py.packets.console_version import (
    ConsoleVersionData,
    ConsoleVersionRequestData,
)

from airtouch5py.packets.datapacket import Data, DataPacket
from airtouch5py.packets.zone_control import (
    ZoneControlData,
    ZoneControlZone,
    ZoneSettingPower,
    ZoneSettingValue,
)
from airtouch5py.packets.zone_name import ZoneName, ZoneNameData, ZoneNameRequestData

from airtouch5py.packets.zone_status import (
    ControlMethod,
    ZonePowerState,
    ZoneStatusData,
    ZoneStatusZone,
)
from bitarray import bitarray
from bitarray.util import ba2int


class PacketDecoder:
    """
    Decode packets from the AirTouch 5 protocol.
    Assumes that they have already been validated (CRC, data length)
    """

    # https://stackoverflow.com/questions/43634618/how-do-i-test-if-int-value-exists-in-python-enum-without-using-try-catch
    _set_ZoneSettingValue = set(item.value for item in ZoneSettingValue)
    _set_ZoneSettingPower = set(item.value for item in ZoneSettingPower)
    _set_SetPowerSetting = set(item.value for item in SetPowerSetting)
    _set_SetAcMode = set(item.value for item in SetAcMode)
    _set_SetAcFanSpeed = set(item.value for item in SetAcFanSpeed)
    _set_SetpointControl = set(item.value for item in SetpointControl)
    _set_AcPowerState = set(item.value for item in AcPowerState)
    _set_AcMode = set(item.value for item in AcMode)
    _set_AcFanSpeed = set(item.value for item in AcFanSpeed)

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
            case MessageType.CONTROL_STATUS.value:
                data = self.decode_control_status(data_bytes)
            case MessageType.EXTENDED.value:
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
            raise ValueError(
                f"Data length does not match expected {normal_data_length + repeat_data_length * repeat_data_count} found {len(bytes) - 8}"
            )

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
                if repeat_data_count != 0 and repeat_data_length != 8:
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
                if repeat_data_count != 0 and repeat_data_length != 10:
                    raise ValueError(
                        "AC status message should have 10 byte repeat data"
                    )
                return self.decode_ac_status(bytes[8:], repeat_data_count)
            case _:
                raise ValueError(f"Unknown sub message type: {hex(sub_message_type)}")

    def decode_zone_control(
        self, bytes: bytes, repeat_data_count: int
    ) -> ZoneControlData:
        zones: list[ZoneControlZone] = []
        bits = bitarray(endian="big")

        for i in range(0, repeat_data_count):
            bits.clear()
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

    def decode_zone_status(
        self, bytes: bytes, repeat_data_count: int
    ) -> ZoneStatusData:
        if repeat_data_count == 0:
            return ZoneStatusData([])

        zones: list[ZoneStatusZone] = []
        bits = bitarray(endian="big")

        for i in range(0, repeat_data_count):
            bits.clear()
            bits.frombytes(bytes[i * 8 : i * 8 + 8])
            # Byte 1 Bit 8-7 Zone power state
            zone_power_state = ZonePowerState(ba2int(bits[0:2]))
            # Byte 1 Bit 6-1 Zone number
            zone_number = ba2int(bits[2:8])
            # Byte 2 Bit 8 Control method
            control_method = ControlMethod(ba2int(bits[8 + 0 : 8 + 1]))
            # Byte 2 Bit 7-1 Open percentage
            open_percentage = ba2int(bits[8 + 1 : 8 + 8]) / 100
            # Byte 3 Set point
            set_point = ba2int(bits[16 : 16 + 8])
            if set_point == 0xFF:  # 0xFF invalid
                set_point = None
            else:
                set_point = (set_point + 100) / 10
            # Byte 4 Bit 8 Has sensor
            has_sensor = bool(bits[24 + 0])
            # Byte 5-6 Temperature
            temperature = (ba2int(bits[32 : 32 + 16]) - 500) / 10
            if temperature > 150:  # temp > 150 invalid
                temperature = None
            # Byte 7 Bit 2 Spill active
            spill_active = bool(bits[48 + 6])
            # Byte 7 Bit 1 Is low battery
            is_low_battery = bool(bits[48 + 7])

            zones.append(
                ZoneStatusZone(
                    zone_power_state,
                    zone_number,
                    control_method,
                    open_percentage,
                    set_point,
                    has_sensor,
                    temperature,
                    spill_active,
                    is_low_battery,
                )
            )
        return ZoneStatusData(zones)

    def decode_ac_control(self, bytes: bytes, repeat_data_count: int) -> AcControlData:
        ac_control: list[AcControl] = []
        bits = bitarray(endian="big")

        for i in range(0, repeat_data_count):
            bits.clear()
            bits.frombytes(bytes[i * 4 : i * 4 + 4])
            # Byte 1 Bit 8-5 Power setting
            power_setting = ba2int(bits[0:4])
            if power_setting in self._set_SetPowerSetting:
                power_setting = SetPowerSetting(power_setting)
            else:
                power_setting = SetPowerSetting.KEEP_POWER_SETTING
            # Byte 1 Bit 4-1 AC number
            ac_number = ba2int(bits[4:8])
            # Byte 2 Bit 8-5 AC mode
            ac_mode = ba2int(bits[8 + 0 : 8 + 4])
            if ac_mode in self._set_SetAcMode:
                ac_mode = SetAcMode(ac_mode)
            else:
                ac_mode = SetAcMode.KEEP_AC_MODE
            # Byte 2 Bit 4-1 AC fan speed
            ac_fan_speed = ba2int(bits[8 + 4 : 8 + 8])
            if ac_fan_speed in self._set_SetAcFanSpeed:
                ac_fan_speed = SetAcFanSpeed(ac_fan_speed)
            else:
                ac_fan_speed = SetAcFanSpeed.KEEP_AC_FAN_SPEED
            # Byte 3 Setpoint control
            setpoint_control = ba2int(bits[16 : 16 + 8])
            if setpoint_control in self._set_SetpointControl:
                setpoint_control = SetpointControl(setpoint_control)
            else:
                setpoint_control = SetpointControl.INVALIDATE_DATA
            # Byte 4 Setpoint value
            setpoint = (ba2int(bits[24 : 24 + 8]) + 100) / 10

            ac_control.append(
                AcControl(
                    power_setting,
                    ac_number,
                    ac_mode,
                    ac_fan_speed,
                    setpoint_control,
                    setpoint,
                )
            )

        return AcControlData(ac_control)

    def decode_ac_status(self, bytes: bytes, repeat_data_count: int) -> AcStatusData:
        if repeat_data_count == 0:
            return AcStatusData([])

        ac_status: list[AcStatus] = []
        bits = bitarray(endian="big")

        for i in range(0, repeat_data_count):
            bits.clear()
            bits.frombytes(bytes[i * 10 : i * 10 + 10])

            # Byte 1 Bit 8-5 AC power state
            ac_power_state = ba2int(bits[0:4])
            if ac_power_state in self._set_AcPowerState:
                ac_power_state = AcPowerState(ac_power_state)
            else:
                ac_power_state = AcPowerState.NOT_AVAILABLE
            # Byte 1 Bit 4-1 AC number
            ac_number = ba2int(bits[4:8])
            # Byte 2 Bit 8-5 AC mode
            ac_mode = ba2int(bits[8 + 0 : 8 + 4])
            if ac_mode in self._set_AcMode:
                ac_mode = AcMode(ac_mode)
            else:
                ac_mode = AcMode.NOT_AVAILABLE
            # Byte 2 Bit 4-1 AC fan speed
            ac_fan_speed = ba2int(bits[8 + 4 : 8 + 8])
            if ac_fan_speed in self._set_AcFanSpeed:
                ac_fan_speed = AcFanSpeed(ac_fan_speed)
            else:
                ac_fan_speed = AcFanSpeed.NOT_AVAILABLE
            # Byte 3 Setpoint
            setpoint = (ba2int(bits[16 : 16 + 8]) + 100) / 10
            # Byte 4 Bit 4 Turbo active
            turbo_active = bool(bits[24 + 4])
            # Byte 4 Bit 3 Bypass active
            bypass_active = bool(bits[24 + 5])
            # Byte 4 Bit 2 Spill active
            spill_active = bool(bits[24 + 6])
            # Byte 4 Bit 1 Timer set
            timer_set = bool(bits[24 + 7])
            # Byte 5-6 Temperature
            temperature = ba2int(bits[32 : 32 + 16])
            if temperature <= 2000:
                temperature = (temperature - 500) / 10
            else:  # Other: Not available
                temperature = None
            # Byte 7-8 Error code
            error_code = ba2int(bits[48 : 48 + 16])

            ac_status.append(
                AcStatus(
                    ac_power_state,
                    ac_number,
                    ac_mode,
                    ac_fan_speed,
                    setpoint,
                    turbo_active,
                    bypass_active,
                    spill_active,
                    timer_set,
                    temperature,
                    error_code,
                )
            )

        return AcStatusData(ac_status)

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
        if len(bytes) == 0:
            return AcAbilityRequestData(None)
        if len(bytes) == 1:
            return AcAbilityRequestData(struct.unpack(">B", bytes[0:1])[0])

        ac_ability: list[AcAbility] = []
        bits = bitarray(endian="big")

        while len(bytes) > 2:
            # Byte 3 AC number
            ac_number = struct.unpack(">B", bytes[0:1])[0]
            # Byte 4 Following data length
            length = struct.unpack(">B", bytes[1:2])[0]
            # Byte 5-20 AC Name (Null terminated if nulls fit)
            name = bytes[2:18].decode("ascii").split("\x00")[0]
            # Byte 21 start zone number
            start_zone_number = struct.unpack(">B", bytes[18:19])[0]
            # Byte 22 zone count
            zone_count = struct.unpack(">B", bytes[19:20])[0]

            bits.clear()
            bits.frombytes(bytes[20:22])
            # Byte 23 Bit 5 Cool mode
            supports_mode_cool = bool(bits[3])
            # Byte 23 Bit 4 Fan mode
            supports_mode_fan = bool(bits[4])
            # Byte 23 Bit 3 Dry mode
            supports_mode_dry = bool(bits[5])
            # Byte 23 Bit 2 Heat mode
            supports_mode_heat = bool(bits[6])
            # Byte 23 Bit 1 Auto mode
            supports_mode_auto = bool(bits[7])
            # Byte 24 Bit 8 Fan speed intelligent auto
            supports_fan_speed_intelligent_auto = bool(bits[8 + 0])
            # Byte 24 Bit 7 Fan speed turbo
            supports_fan_speed_turbo = bool(bits[8 + 1])
            # Byte 24 Bit 6 Fan speed powerful
            supports_fan_speed_powerful = bool(bits[8 + 2])
            # Byte 24 Bit 5 Fan speed high
            supports_fan_speed_high = bool(bits[8 + 3])
            # Byte 24 Bit 4 Fan speed medium
            supports_fan_speed_medium = bool(bits[8 + 4])
            # Byte 24 Bit 3 Fan speed low
            supports_fan_speed_low = bool(bits[8 + 5])
            # Byte 24 Bit 2 Fan speed quiet
            supports_fan_speed_quiet = bool(bits[8 + 6])
            # Byte 24 Bit 1 Fan speed auto
            supports_fan_speed_auto = bool(bits[8 + 7])

            # Byte 25 Min cool set point
            min_cool_set_point = struct.unpack(">B", bytes[22:23])[0]
            # Byte 26 Max cool set point
            max_cool_set_point = struct.unpack(">B", bytes[23:24])[0]
            # Byte 27 Min heat set point
            min_heat_set_point = struct.unpack(">B", bytes[24:25])[0]
            # Byte 28 Max heat set point
            max_heat_set_point = struct.unpack(">B", bytes[25:26])[0]

            ac_ability.append(
                AcAbility(
                    ac_number,
                    name,
                    start_zone_number,
                    zone_count,
                    supports_mode_cool,
                    supports_mode_fan,
                    supports_mode_dry,
                    supports_mode_heat,
                    supports_mode_auto,
                    supports_fan_speed_intelligent_auto,
                    supports_fan_speed_turbo,
                    supports_fan_speed_powerful,
                    supports_fan_speed_high,
                    supports_fan_speed_medium,
                    supports_fan_speed_low,
                    supports_fan_speed_quiet,
                    supports_fan_speed_auto,
                    min_cool_set_point,
                    max_cool_set_point,
                    min_heat_set_point,
                    max_heat_set_point,
                )
            )

            # We've now used the first 2 + length bytes, so remove them from the buffer
            bytes = bytes[2 + length :]

        return AcAbilityData(ac_ability)

    def decode_ac_error_information(self, bytes: bytes) -> Data:
        # Byte 3 AC number
        ac_number = struct.unpack(">B", bytes[0:1])[0]
        if len(bytes) == 1:
            return AcErrorInformationRequestData(ac_number)

        # Byte 4 error info length
        error_length = struct.unpack(">B", bytes[1:2])[0]
        # Byte 5-error_length error info
        error_info = bytes[2 : 2 + error_length].decode("ascii")
        return AcErrorInformationData(ac_number, error_info)

    def decode_zone_name(self, bytes: bytes) -> Data:
        if len(bytes) == 0:
            return ZoneNameRequestData(None)
        if len(bytes) == 1:
            return ZoneNameRequestData(struct.unpack(">B", bytes[0:1])[0])

        names: list[ZoneName] = []

        while len(bytes) > 2:
            # Byte 3 Zone number
            zone_number = struct.unpack(">B", bytes[0:1])[0]
            # Byte 4 Name  length
            length = struct.unpack(">B", bytes[1:2])[0]
            # Byte 5..n Zone Name
            name = bytes[2 : 2 + length].decode("ascii")

            names.append(ZoneName(zone_number, name))
            # We've now used the first 2 + length bytes, so remove them from the buffer
            bytes = bytes[2 + length :]

        return ZoneNameData(names)

    def decode_console_version(self, bytes: bytes) -> Data:
        if len(bytes) == 0:
            return ConsoleVersionRequestData()

        # Byte 3 Update sign (0 - latest, Other - new version)
        has_update = struct.unpack(">B", bytes[0:1])[0] != 0
        # Byte 4 version string length
        length = struct.unpack(">B", bytes[1:2])[0]
        # Byte 5..n Version string
        version = bytes[2 : 2 + length].decode("ascii")

        return ConsoleVersionData(has_update, version)
