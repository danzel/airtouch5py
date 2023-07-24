import asyncio
import logging
from enum import Enum

from airtouch5py.data_packet_factory import DataPacketFactory

from airtouch5py.packet_encoder import PacketEncoder
from airtouch5py.packet_reader import PacketReader

from airtouch5py.packets.datapacket import DataPacket

_LOGGER = logging.getLogger(__name__)


class Airtouch5ConnectionStateChange(Enum):
    CONNECTED = 1
    DISCONNECTED = 2


class Airtouch5Client:
    """
    The "Raw" (Hard mode) Airtouch 5 Client.
    You should probably use Airtouch5SimpleClient instead.

    Usage:
    Construct, call connect.
    Wait on packets_received to receive a CONNECTED message.
    Wait on updates from packets_received, use send_packet to send packets.

    Call disconnect to disconnect.

    When a DISCONNECTED message is received, call connect to reconnect.
    """

    _encoder = PacketEncoder()
    _packet_reader = PacketReader()

    ip: str
    packets_received: asyncio.Queue[Airtouch5ConnectionStateChange | DataPacket]

    _reader: asyncio.StreamReader | None
    _writer: asyncio.StreamWriter | None

    def __init__(self, ip: str):
        self.ip = ip
        self.packets_received = asyncio.Queue()
        self.data_packet_factory = DataPacketFactory()

        self._connected = False
        self._should_be_connected = False
        self._writer, self._reader = None, None

    async def connect(self):
        """
        Connect to the airtouch 5.
        Times out after 5 seconds.
        Throws if we fail to connect.
        Otherwise puts a connected message in the queue and starts up the reader task.
        """
        _LOGGER.info(f"Connecting to {self.ip}:9005")
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.ip, 9005), 5
        )
        _LOGGER.info(f"Connected to {self.ip}:9005")

        self.packets_received.put_nowait(Airtouch5ConnectionStateChange.CONNECTED)
        self._reader_task = asyncio.create_task(self._read_packets())

    async def disconnect(self):
        writer = self._writer

        if writer is not None:
            writer.close()
            await writer.wait_closed()
            self._writer, self._reader = None, None

        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None

    async def _read_packets(self):
        """
        Continuously read packets from the socket and put them in the queue.
        """
        reader = self._reader
        if reader is None:
            raise Exception("Reader is None")

        while reader.at_eof() == False:
            read = await reader.read(1024)
            print(f"read packets read {len(read)} bytes")
            packets = self._packet_reader.read(read)
            print(
                f"read packets found {len(packets)} packets, bytes remaining {len(self._packet_reader._buffer)}"
            )
            for packet in packets:
                self.packets_received.put_nowait(packet)

    # TODO: Do we need to lock?
    async def send_packet(self, packet: DataPacket):
        """
        Send the given packet to the airtouch 5.
        Throws if we aren't connected
        """
        writer = self._writer
        if writer is None:
            raise Exception("Writer is None")

        _LOGGER.debug(f"Sending packet {packet}")
        writer.write(self._encoder.encode(packet))
        await writer.drain()
