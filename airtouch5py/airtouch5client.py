import asyncio
import logging
from enum import Enum

from airtouch5py.data_packet_factory import DataPacketFactory

from airtouch5py.packet_encoder import PacketEncoder
from airtouch5py.packet_reader import PacketReader
from airtouch5py.packets.console_version import ConsoleVersionData

from airtouch5py.packets.datapacket import DataPacket


class Airtouch5ConnectionStateChange(Enum):
    CONNECTED = 1
    DISCONNECTED = 2


class Airtouch5Client:
    """
    Usage:
    Construct, call connect.
    Wait on packets_received to receive a Connected message.
    Wait on updates from packets_received, use send_packet to send packets.

    Call disconnect to disconnect.
    """

    _logger = logging.getLogger(__name__)
    _encoder = PacketEncoder()
    _packet_reader = PacketReader()

    ip: str
    data_packet_factory: DataPacketFactory
    packets_received: asyncio.Queue[Airtouch5ConnectionStateChange | DataPacket]

    _connected: bool
    _should_be_connected: bool
    _reader: asyncio.StreamReader | None
    _writer: asyncio.StreamWriter | None

    def __init__(self, ip: str):
        self.ip = ip
        self.packets_received = asyncio.Queue()
        self.data_packet_factory = DataPacketFactory()

        self._connected = False
        self._should_be_connected = False
        self._writer, self._reader = None, None

    def connect(self):
        """
        Connect to the airtouch 5, and handle reconnecting in the future if we disconnect.
        Returns when connect, else throws
        """
        self._should_be_connected = True
        self._connection_task = asyncio.create_task(self._connect())

    async def disconnect(self):
        self._should_be_connected = False
        writer = self._writer
        if writer is not None:
            writer.close()
            await writer.wait_closed()

    async def _connect(self):
        while self._should_be_connected:
            try:
                self._reader, self._writer = None, None

                self._logger.info(f"Connecting to {self.ip}:9005")
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.ip, 9005), 5
                )
                self._logger.info(
                    f"TCP connected to {self.ip}:9005, verifying connection"
                )

                # Send a console version request Packet to verify we are connected to an airtouch 5
                # If we don't get a response in 5 seconds assume this isn't right and disconnect
                # Discard any other packets received before we receive the response
                await self.send_packet(
                    self.data_packet_factory.console_version_request()
                )

                # Wait for the response
                start_wait = asyncio.get_running_loop().time()
                got_response = False
                while (
                    asyncio.get_running_loop().time() - start_wait < 5
                    and not got_response
                ):
                    packets = await asyncio.wait_for(
                        self._read_packets_once(self._reader), 5
                    )
                    for packet in packets:
                        if type(packet.data) is ConsoleVersionData:
                            got_response = True
                            break

                if not got_response:
                    raise Exception("Did not receive console version response")

                # Otherwise it is time to set up the reader task
                self._logger.info(f"Connected to {self.ip}:9005")
                self._reader_task = asyncio.create_task(self._read_packets())

                self._connected = True
                self.packets_received.put_nowait(
                    Airtouch5ConnectionStateChange.CONNECTED
                )
                await self._writer.wait_closed()
            except BaseException as e:
                self._logger.warning(
                    f"Failed to connect to {self.ip}:9005: {e}. Will retry in 5 seconds"
                )

            # Let listener know we have disconnected
            if self._connected:
                self._connected = False
                self.packets_received.put_nowait(
                    Airtouch5ConnectionStateChange.DISCONNECTED
                )

            # Close the socket if it is still around
            if self._writer is not None:
                self._writer.close()
                self._reader, self._writer = None, None

            if self._should_be_connected:
                await asyncio.sleep(5)

    async def _read_packets_once(self, reader: asyncio.StreamReader):
        read = await reader.read(1024)
        return self._packet_reader.read(read)

    async def _read_packets(self):
        """
        Continuously read packets from the socket and put them in the queue.
        """
        reader = self._reader
        if reader is None:
            raise Exception("Reader is None")

        while reader.at_eof() == False:
            packets = await self._read_packets_once(reader)
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

        self._logger.debug(f"Sending packet {packet}")
        writer.write(self._encoder.encode(packet))
        await writer.drain()
