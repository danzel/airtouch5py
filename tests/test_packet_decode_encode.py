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


def test_decode_encode_zone_status_request_example():
    source_data = b"\x55\x55\x55\xAA\x80\xB0\x01\xC0\x00\x08\x21\x00\x00\x00\x00\x00\x00\x00\xA4\x31"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_status_response_example():
    source_data = b"\x55\x55\x55\xAA\xB0\x80\x01\xC0\x00\x18\x21\x00\x00\x00\x00\x08\x00\x02\x40\x80\x96\x80\x02\xE7\x00\x00\x01\x64\xFF\x00\x07\xFF\x00\x00\xB9\xEF"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_control_turn_off_second_ac_example():
    source_data = b"\x55\x55\x55\xAA\x80\xb0\x01\xC0\x00\x0C\x22\x00\x00\x00\x00\x04\x00\x01\x21\xFF\x00\xFF\xD3\x47"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_control_first_ac_cool_second_ac_26_degrees_example():
    source_data = b"\x55\x55\x55\xAA\x80\xb0\x01\xC0\x00\x10\x22\x00\x00\x00\x00\x04\x00\x02\x00\x4F\x00\xFF\x01\xFF\x40\xA0\x10\x4B"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_status_request_example():
    source_data = b"\x55\x55\x55\xAA\x80\xB0\x01\xC0\x00\x08\x23\x00\x00\x00\x00\x00\x00\x00\x7D\xB0"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_status_response_2_acs_example():
    source_data = b"\x55\x55\x55\xAA\xB0\x80\x01\xC0\x00\x1C\x23\x00\x00\x00\x00\x0A\x00\x02\x10\x12\x78\xC0\x02\xDA\x00\x00\x80\x00\x01\x42\x64\xC0\x02\xE4\x00\x00\x80\x00\x3D\x79"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_extended_ac_ability_request_example():
    source_data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x03\xFF\x11\x00\x09\x83"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_extended_ac_ability_response_example():
    source_data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x1C\xFF\x11\x00\x18\x55\x4E\x49\x54\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x17\x1D\x10\x1f\x12\x1f\xa2\x26"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_error_information_request_example():
    source_data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x03\xFF\x10\x00\x99\x82"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_ac_error_information_response_example():
    source_data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x0C\xFF\x10\x00\x08\x45\x52\x3A\x20\x46\x46\x46\x45\x36\xE4"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_names_request_all_example():
    source_data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x02\xFF\x13\x42\xCD"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_encode_zone_names_request_single_example():
    source_data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x03\xFF\x13\x00\x69\x82"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_zone_names_response_single_example():
    source_data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x0A\xFF\x13\x00\x06\x4C\x69\x76\x69\x6E\x67\xB6\x2F"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_zone_names_response_multiple_example():
    source_data = b"\x55\x55\x55\xAA\xb0\x90\x01\x1F\x00\x1C\xFF\x13\x00\x06\x4C\x69\x76\x69\x6E\x67\x01\x07\x4B\x69\x74\x63\x68\x65\x6E\x02\x07\x42\x65\x64\x72\x6F\x6F\x6D\xAE\x8B"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_decode_console_version_request_example():
    source_data = b"\x55\x55\x55\xAA\x90\xB0\x01\x1F\x00\x02\xFF\x30\x9B\x8C"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data


def test_console_version_response_example():
    source_data = b"\x55\x55\x55\xAA\xB0\x90\x01\x1F\x00\x0F\xFF\x30\x00\x0B\x31\x2E\x30\x2E\x33\x2C\x31\x2E\x30\x2E\x33\x13\x28"
    encoded = decode_then_encode(source_data)
    assert encoded == source_data
