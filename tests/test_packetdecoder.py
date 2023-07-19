from airtouch5py.packetdecoder import PacketDecoder
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_control import (
    ZoneControlData,
    ZoneSettingPower,
    ZoneSettingValue,
)


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
