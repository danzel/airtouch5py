from airtouch5py.packet_reader import PacketReader


def test_read_zone_control_example():
    source_data = b"\x55\x55\x55\xAA\x80\xB0\x0F\xC0\x00\x0C\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xFF\x00\xF0\xA1"
    reader = PacketReader()
    packets = reader.read(source_data)

    assert len(packets) == 1


def test_read_zone_control_one_byte_at_a_time_example():
    source_data = b"\x55\x55\x55\xAA\x80\xB0\x0F\xC0\x00\x0C\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xFF\x00\xF0\xA1"
    reader = PacketReader()

    # Shouldn't be any packets in here
    for i in range(len(source_data) - 1):
        packets = reader.read(source_data[i : i + 1])
        assert len(packets) == 0

    # Until we've read the last byte
    packets = reader.read(source_data[len(source_data) - 1 :])
    assert len(packets) == 1


def test_read_two_zone_control_example():
    source_data = b"\x55\x55\x55\xAA\x80\xB0\x0F\xC0\x00\x0C\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xFF\x00\xF0\xA1"
    source_data += source_data
    reader = PacketReader()
    packets = reader.read(source_data)

    assert len(packets) == 2
