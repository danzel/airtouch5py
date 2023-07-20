# Test the packet encoder by decoding and then encoding a packet and comparing the result to the original bytes

from airtouch5py.packet_decoder import PacketDecoder
from airtouch5py.packet_encoder import PacketEncoder
from airtouch5py.packets.datapacket import DataPacket


def decode_then_encode(source_data: bytes) -> bytes:
    decoder = PacketDecoder()
    packet: DataPacket = decoder.decode(source_data)

    encoder = PacketEncoder()
    encoded = encoder.encode(packet)

    return encoded


def test_decode_encode_zone_control_example():
    source_data = b"\x55\x55\x55\xAA\x80\xB0\x0F\xC0\x00\x0C\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xFF\x00\xF0\xA1"

    encoded = decode_then_encode(source_data)

    assert encoded == source_data
