import asyncio
import logging

from airtouch5py.packet_encoder import PacketEncoder
from airtouch5py.packet_reader import PacketReader

from airtouch5py.packets.datapacket import DataPacket


class Airtouch5Client:
    ip: str
    _logger = logging.getLogger(__name__)

    _reader: asyncio.StreamReader
    _writer: asyncio.StreamWriter

    _encoder = PacketEncoder()
    _packet_reader = PacketReader()

    packets_received: asyncio.Queue[DataPacket] = asyncio.Queue()

    def __init__(self, ip: str):
        self.ip = ip

    async def connect(self):
        self._logger.info(f"Connecting to {self.ip}:9005")
        self._reader, self._writer = await asyncio.open_connection(self.ip, 9005)
        self._logger.info(f"Connected to {self.ip}:9005")

        self._reader_task = asyncio.create_task(self._read_packets())

    async def _read_packets(self):
        """
        Continuously read packets from the socket and put them in the queue.
        """
        while self._reader.at_eof() == False:
            read = await self._reader.read(1024)
            packets = self._packet_reader.read(read)
            for packet in packets:
                self.packets_received.put_nowait(packet)

    # TODO: Do we need to lock?
    async def send_packet(self, packet: DataPacket):
        self._logger.debug(f"Sending packet {packet}")
        self._writer.write(self._encoder.encode(packet))
        await self._writer.drain()
