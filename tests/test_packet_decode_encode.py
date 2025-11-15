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
    source_data = b"\x55\x55\x55\xaa\x80\xb0\x0f\xc0\x00\x0c\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xff\x00\xf0\xa1"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_status_request_example():
    source_data = b"\x55\x55\x55\xaa\x80\xb0\x01\xc0\x00\x08\x21\x00\x00\x00\x00\x00\x00\x00\xa4\x31"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_status_response_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x80\x01\xc0\x00\x18\x21\x00\x00\x00\x00\x08\x00\x02\x40\x80\x96\x80\x02\xe7\x00\x00\x01\x64\xff\x00\x07\xff\x00\x00\xb9\xef"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_control_turn_off_second_ac_example():
    source_data = b"\x55\x55\x55\xaa\x80\xb0\x01\xc0\x00\x0c\x22\x00\x00\x00\x00\x04\x00\x01\x21\xff\x00\xff\xd3\x47"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_control_first_ac_cool_second_ac_26_degrees_example():
    source_data = b"\x55\x55\x55\xaa\x80\xb0\x01\xc0\x00\x10\x22\x00\x00\x00\x00\x04\x00\x02\x00\x4f\x00\xff\x01\xff\x40\xa0\x10\x4b"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_status_request_example():
    source_data = b"\x55\x55\x55\xaa\x80\xb0\x01\xc0\x00\x08\x23\x00\x00\x00\x00\x00\x00\x00\x7d\xb0"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_status_response_2_acs_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x80\x01\xc0\x00\x1c\x23\x00\x00\x00\x00\x0a\x00\x02\x10\x12\x78\xc0\x02\xda\x00\x00\x80\x00\x01\x42\x64\xc0\x02\xe4\x00\x00\x80\x00\x3d\x79"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_extended_ac_ability_request_example():
    source_data = b"\x55\x55\x55\xaa\x90\xb0\x01\x1f\x00\x03\xff\x11\x00\x09\x83"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_extended_ac_ability_response_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x90\x01\x1f\x00\x1c\xff\x11\x00\x18\x55\x4e\x49\x54\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x17\x1d\x10\x1f\x12\x1f\xa2\x26"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_error_information_request_example():
    source_data = b"\x55\x55\x55\xaa\x90\xb0\x01\x1f\x00\x03\xff\x10\x00\x99\x82"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_error_information_response_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x90\x01\x1f\x00\x0c\xff\x10\x00\x08\x45\x52\x3a\x20\x46\x46\x46\x45\x36\xe4"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_names_request_all_example():
    source_data = b"\x55\x55\x55\xaa\x90\xb0\x01\x1f\x00\x02\xff\x13\x42\xcd"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_names_request_single_example():
    source_data = b"\x55\x55\x55\xaa\x90\xb0\x01\x1f\x00\x03\xff\x13\x00\x69\x82"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_zone_names_response_single_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x90\x01\x1f\x00\x0a\xff\x13\x00\x06\x4c\x69\x76\x69\x6e\x67\xb6\x2f"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_zone_names_response_multiple_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x90\x01\x1f\x00\x1c\xff\x13\x00\x06\x4c\x69\x76\x69\x6e\x67\x01\x07\x4b\x69\x74\x63\x68\x65\x6e\x02\x07\x42\x65\x64\x72\x6f\x6f\x6d\xae\x8b"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_console_version_request_example():
    source_data = b"\x55\x55\x55\xaa\x90\xb0\x01\x1f\x00\x02\xff\x30\x9b\x8c"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_console_version_response_example():
    source_data = b"\x55\x55\x55\xaa\xb0\x90\x01\x1f\x00\x0f\xff\x30\x00\x0b\x31\x2e\x30\x2e\x33\x2c\x31\x2e\x30\x2e\x33\x13\x28"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data
