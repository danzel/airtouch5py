from airtouch5py.packetdecoder import PacketDecoder
from airtouch5py.packets.ac_ability import AcAbilityData, AcAbilityRequestData
from airtouch5py.packets.ac_control import (
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
from airtouch5py.packets.ac_status import AcFanSpeed, AcMode, AcPowerState, AcStatusData
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_control import (
    ZoneControlData,
    ZoneSettingPower,
    ZoneSettingValue,
)
from airtouch5py.packets.zone_name import ZoneNameData, ZoneNameRequestData
from airtouch5py.packets.zone_status import (
    ControlMethod,
    ZonePowerState,
    ZoneStatusData,
)

"""
Tests for PacketDecoder, using examples from the protocol documentation
"""


def test_decode_zone_control_example():
    """
    Decode the zone control message as given in the protocol documentation.
    Turn off the second zone
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x80\xB0\x0F\xC0\x00\x0C\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xFF\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x80B0
    assert packet.message_id == 0x0F
    assert type(packet.data) is ZoneControlData

    # Zone control
    d: ZoneControlData = packet.data
    assert len(d.zones) == 1

    # Zone
    z = d.zones[0]
    assert z.zone_number == 1
    assert z.zone_setting_value == ZoneSettingValue.KEEP_SETTING_VALUE
    assert z.power == ZoneSettingPower.SET_TO_OFF
    assert z.value_to_set == 0xFF


def test_decode_zone_status_request_example():
    """
    Decode the zone status (request) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x80\xB0\x01\xC0\x00\x08\x21\x00\x00\x00\x00\x00\x00\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x80B0
    assert packet.message_id == 0x01
    assert type(packet.data) is ZoneStatusData

    # Zone status
    assert len(packet.data.zones) == 0


def test_decode_zone_status_response_example():
    """
    Decode the zone status (response) message as given in the protocol documentation.

    Data has been altered to be valid (Example has 2 zones worth of data but says it just has 1)
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\xB0\x80\x01\xC0\x00\x18\x21\x00\x00\x00\x00\x08\x00\x02\x40\x80\x96\x80\x02\xE7\x00\x00\x01\x64\xFF\x00\x07\xFF\x00\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0xB080
    assert packet.message_id == 0x01
    assert type(packet.data) is ZoneStatusData

    # Zone status
    assert len(packet.data.zones) == 2

    # Zone 0
    zone = packet.data.zones[0]
    assert zone.zone_power_state == ZonePowerState.ON
    assert zone.zone_number == 0
    assert zone.control_method == ControlMethod.TEMPERATURE_CONTROL
    assert zone.open_percentage == 0.0
    assert zone.set_point == 25
    assert zone.has_sensor == True
    assert zone.temperature == 24.3
    assert zone.spill_active == False
    assert zone.is_low_battery == False

    # Zone 1
    zone = packet.data.zones[1]
    assert zone.zone_power_state == ZonePowerState.OFF
    assert zone.zone_number == 1
    assert zone.control_method == ControlMethod.PERCENTAGE_CONTROL
    assert zone.open_percentage == 1.0
    assert zone.set_point == None  # Invalid
    assert zone.has_sensor == False
    assert zone.temperature == None  # Invalid
    assert zone.spill_active == False
    assert zone.is_low_battery == False


def test_ac_control_turn_off_second_ac():
    """
    Decode the AC control message as given in the protocol documentation.

    Turn off the second AC
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x80\xb0\x01\xC0\x00\x0C\x22\x00\x00\x00\x00\x04\x00\x01\x21\xFF\x00\xFF"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x80B0
    assert packet.message_id == 0x01
    assert type(packet.data) is AcControlData

    # AC control
    assert len(packet.data.ac_control) == 1

    # AC
    c = packet.data.ac_control[0]
    assert c.power_setting == SetPowerSetting.SET_TO_OFF
    assert c.ac_number == 1
    assert c.ac_mode == SetAcMode.KEEP_AC_MODE
    assert c.ac_fan_speed == SetAcFanSpeed.KEEP_AC_FAN_SPEED
    assert c.setpoint_control == SetpointControl.KEEP_SETPOINT_VALUE
    # Value of setpoint isn't used in this case (It is 0xFF), but checking we still decode it fine
    assert c.setpoint == 35.5


def test_ac_control_first_ac_cool_second_ac_26_degrees():
    """
    Decode the AC control message as given in the protocol documentation.

    Set the first AC to cool and the second AC to 26 degrees
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x80\xb0\x01\xC0\x00\x10\x22\x00\x00\x00\x00\x04\x00\x02\x00\x4F\x00\xFF\x01\xFF\x40\xA0"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x80B0
    assert packet.message_id == 0x01
    assert type(packet.data) is AcControlData

    # AC control
    assert len(packet.data.ac_control) == 2

    # AC 0
    c = packet.data.ac_control[0]
    assert c.power_setting == SetPowerSetting.KEEP_POWER_SETTING
    assert c.ac_number == 0
    assert c.ac_mode == SetAcMode.SET_TO_COOL
    assert c.ac_fan_speed == SetAcFanSpeed.KEEP_AC_FAN_SPEED
    assert c.setpoint_control == SetpointControl.KEEP_SETPOINT_VALUE
    assert c.setpoint == 35.5  # Unused in this case

    # AC 1
    c = packet.data.ac_control[1]
    assert c.power_setting == SetPowerSetting.KEEP_POWER_SETTING
    assert c.ac_number == 1
    assert c.ac_mode == SetAcMode.KEEP_AC_MODE
    assert c.ac_fan_speed == SetAcFanSpeed.KEEP_AC_FAN_SPEED
    assert c.setpoint_control == SetpointControl.CHANGE_SETPOINT
    assert c.setpoint == 26.0


def test_ac_status_request():
    """
    Decode the AC status (request) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x80\xB0\x01\xC0\x00\x08\x23\x00\x00\x00\x00\x00\x00\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x80B0
    assert packet.message_id == 0x01
    assert type(packet.data) is AcStatusData

    # AC status
    assert len(packet.data.ac_status) == 0


def test_ac_status_response_2_acs():
    """
    Decode the AC status (response) message as given in the protocol documentation.

    AirTouch 5 response with data for 2 ACs
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\xB0\x80\x01\xC0\x00\x1C\x23\x00\x00\x00\x00\x0A\x00\x02\x10\x12\x78\xC0\x02\xDA\x00\x00\x80\x00\x01\x42\x64\xC0\x02\xE4\x00\x00\x80\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0xB080
    assert packet.message_id == 0x01
    assert type(packet.data) is AcStatusData

    # AC status
    assert len(packet.data.ac_status) == 2

    # AC 0
    ac = packet.data.ac_status[0]
    assert ac.ac_power_state == AcPowerState.ON
    assert ac.ac_number == 0
    assert ac.ac_mode == AcMode.HEAT
    assert ac.ac_fan_speed == AcFanSpeed.LOW
    assert ac.ac_setpoint == 22.0
    assert ac.turbo_active == False
    assert ac.bypass_active == False
    assert ac.spill_active == False
    assert ac.timer_set == False
    assert ac.temperature == 23.0
    assert ac.error_code == 0  # No error

    # AC 1
    ac = packet.data.ac_status[1]
    assert ac.ac_power_state == AcPowerState.OFF
    assert ac.ac_number == 1
    assert ac.ac_mode == AcMode.COOL
    assert ac.ac_fan_speed == AcFanSpeed.LOW
    assert ac.ac_setpoint == 20.0
    assert ac.turbo_active == False
    assert ac.bypass_active == False
    assert ac.spill_active == False
    assert ac.timer_set == False
    assert ac.temperature == 24.0
    assert ac.error_code == 0  # No error


def test_extended_ac_ability_request():
    """
    Decode the extended AC ability (request) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x03\xFF\x11\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x90B0
    assert packet.message_id == 0x01
    assert type(packet.data) is AcAbilityRequestData

    # AC ability request (AC 0)
    assert packet.data.ac_number == 0x00


def test_extended_ac_ability_response():
    """
    Decode the extended AC ability (response) message as given in the protocol documentation.

    Had to increase length to 1C from 1A
    Sample says the AC supports fan, but it doesn't
    Sample says the AC doesn't support dry, but it does
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x1C\xFF\x11\x00\x18\x55\x4E\x49\x54\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x17\x1D\x10\x1f\x12\x1f"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0xB090
    assert packet.message_id == 0x01
    assert type(packet.data) is AcAbilityData
    assert len(packet.data.ac_ability) == 1

    # AC ability response (AC 0)
    ac = packet.data.ac_ability[0]
    assert ac.ac_number == 0x00
    assert ac.ac_name == "UNIT"
    assert ac.start_zone_number == 0x00
    assert ac.zone_count == 0x04
    assert ac.supports_mode_cool == True
    assert ac.supports_mode_fan == False
    assert ac.supports_mode_dry == True
    assert ac.supports_mode_heat == True
    assert ac.supports_mode_auto == True

    assert ac.supports_fan_speed_intelligent_auto == False
    assert ac.supports_fan_speed_turbo == False
    assert ac.supports_fan_speed_powerful == False
    assert ac.supports_fan_speed_high == True
    assert ac.supports_fan_speed_medium == True
    assert ac.supports_fan_speed_low == True
    assert ac.supports_fan_speed_quiet == False
    assert ac.supports_fan_speed_auto == True

    assert ac.min_cool_set_point == 16.0
    assert ac.max_cool_set_point == 31.0
    assert ac.min_heat_set_point == 18.0
    assert ac.max_heat_set_point == 31.0


def test_ac_error_information_request():
    """
    Decode the AC error information (request) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x03\xFF\x10\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x90B0
    assert packet.message_id == 0x01
    assert type(packet.data) is AcErrorInformationRequestData

    # AC error information request (AC 0)
    assert packet.data.ac_number == 0x00


def test_ac_error_information_response():
    """
    Decode the AC error information (response) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x1A\xFF\x10\x00\x08\x45\x52\x3A\x20\x46\x46\x46\x45"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0xB090
    assert packet.message_id == 0x01
    assert type(packet.data) is AcErrorInformationData

    # AC error information response (AC 0)
    assert packet.data.ac_number == 0x00
    assert packet.data.error_info == "ER: FFFE"


def test_zone_names_request_all():
    """
    Decode the zone names (request) message as given in the protocol documentation.

    TODO: The docs also say this is 0xFF 0x12?? In the samples they use both.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x02\xFF\x13"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x90B0
    assert packet.message_id == 0x01
    assert type(packet.data) is ZoneNameRequestData

    # All Zones
    assert packet.data.zone_number == None


def test_zone_names_request_single():
    """
    Decode the zone names (request) message as given in the protocol documentation.

    TODO: The docs also say this is 0xFF 0x12?? In the samples they use both.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x03\xFF\x13\x00"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0x90B0
    assert packet.message_id == 0x01
    assert type(packet.data) is ZoneNameRequestData

    # Zone 0
    assert packet.data.zone_number == 0x00


def test_zone_names_response_single():
    """
    Decode the zone names (response) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x0A\xFF\x13\x00\x06\x4C\x69\x76\x69\x6E\x67"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0xB090
    assert packet.message_id == 0x01
    assert type(packet.data) is ZoneNameData
    assert len(packet.data.zone_names) == 1

    # Zone 0
    z = packet.data.zone_names[0]
    assert z.zone_number == 0x00
    assert z.zone_name == "Living"


def test_zone_names_response_multiple():
    """
    Decode the zone names (response) message as given in the protocol documentation.
    """

    decoder = PacketDecoder()
    # TODO: Add CRC bytes
    data = b"\x55\x55\x55\xAA\xb0\x90\x01\x1F\x00\x1D\xFF\x13\x00\x06\x4C\x69\x76\x69\x6E\x67\x01\x07\x4B\x69\x74\x63\x68\x65\x6E\x02\x07\x42\x65\x64\x72\x6F\x6F\x6D"
    packet: DataPacket = decoder.decode(data)

    # Packet
    assert packet.address == 0xB090
    assert packet.message_id == 0x01
    assert type(packet.data) is ZoneNameData
    assert len(packet.data.zone_names) == 3

    # Zone 0
    z = packet.data.zone_names[0]
    assert z.zone_number == 0x00
    assert z.zone_name == "Living"

    # Zone 1
    z = packet.data.zone_names[1]
    assert z.zone_number == 0x01
    assert z.zone_name == "Kitchen"

    # Zone 2
    z = packet.data.zone_names[2]
    assert z.zone_number == 0x02
    assert z.zone_name == "Bedroom"
