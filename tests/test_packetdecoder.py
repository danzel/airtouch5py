from airtouch5py.packetdecoder import PacketDecoder
from airtouch5py.packets.ac_control import (
    AcControlData,
    SetAcFanSpeed,
    SetAcMode,
    SetpointControl,
    SetPowerSetting,
)
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_control import (
    ZoneControlData,
    ZoneSettingPower,
    ZoneSettingValue,
)
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
