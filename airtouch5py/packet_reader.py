import logging

from airtouch5py.packet_decoder import PacketDecoder
from airtouch5py.packets.datapacket import DataPacket

_LOGGER = logging.getLogger(__name__)

# Header (4) + Address (2) + Message Id (1) + Message type (1) + Data length (2) + check bytes (2)
MINIMUM_PACKET_LENGTH = 12
HEADER = b"\x55\x55\x55\xAA"


class PacketReader:
    """
    Provide the bytes received from the airtouch 5 socket, and this class will find the packets, decode them, and return them.
    """

    _buffer: bytearray
    _packet_decoder = PacketDecoder()

    def __init__(self):
        self._buffer = bytearray()

    def read(self, data: bytes) -> list[DataPacket]:
        """
        Read the data and return a list of packets.
        """
        self._buffer.extend(data)

        packets = []

        # h. Redundant bytes in message
        # To prevent the message from containing the same data as header, a 00 is inserted after every three
        # consecutive 0x55s in the message. The inserted 00 is redundant bytes
        # ^^ In testing this actually doesn't happen. I named a zone UUUUUUU and it didn't insert any 00s

        while len(self._buffer) >= MINIMUM_PACKET_LENGTH:
            # Seek until we find the header
            while len(self._buffer) > 0 and not self._buffer.startswith(HEADER):
                self._buffer.pop(0)

            # If we don't have enough data for a packet, then we can't do anything
            if len(self._buffer) < MINIMUM_PACKET_LENGTH:
                break

            # Check if we have a full packet (Data length is now bytes 9-10)
            data_length = int.from_bytes(self._buffer[8:10], byteorder="big")
            packet_length = data_length + MINIMUM_PACKET_LENGTH
            if len(self._buffer) < packet_length:
                break

            # Decode the packet
            try:
                packet = self._packet_decoder.decode(self._buffer[:packet_length])
                packets.append(packet)
            except Exception as e:
                _LOGGER.debug(f"Error decoding packet: {e}")

            # remove the packet from the buffer
            self._buffer = self._buffer[packet_length:]

        return packets
