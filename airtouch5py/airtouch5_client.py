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

    _disconnect_lock: asyncio.Lock

    def __init__(self, ip: str):
        self.ip = ip
        self.packets_received = asyncio.Queue()
        self.data_packet_factory = DataPacketFactory()

        self._connected = False
        self._should_be_connected = False
        self._writer, self._reader = None, None
        self._disconnect_lock = asyncio.Lock()

    async def connect(self):
        """
        Connect to the airtouch 5.
        Times out after 5 seconds.
        Throws if we fail to connect.
        Otherwise puts a connected message in the queue and starts up the reader task.
        """

        # Clear the queue before we connect (Might be dangling stuff in it from a previous connection)
        while not self.packets_received.empty():
            self.packets_received.get_nowait()

        _LOGGER.info(f"Connecting to {self.ip}:9005")
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.ip, 9005), 5
        )
        _LOGGER.info(f"Connected to {self.ip}:9005")

        self.packets_received.put_nowait(Airtouch5ConnectionStateChange.CONNECTED)
        self._reader_task = asyncio.create_task(self._read_packets())

    async def disconnect(self):
        """
        Disconnect the socket if it is connected.
        If stop_reader_task is true, also stop the reader task (Normally you should do this, unless called from the reader task)
        Pushes a DISCONNECTED message in to the queue if we actually disconnected (were connected before)
        """
        async with self._disconnect_lock:
            did_disconnect = False
            if self._writer is not None:
                did_disconnect = True
                self._writer.close()
                try:
                    await self._writer.wait_closed()
                except Exception:
                    # Ignore exceptions when closing
                    _LOGGER.debug("Exception when closing writer", exc_info=True)

            if self._reader_task is not None:
                self._reader_task.cancel()
                self._reader_task = None

            self._writer, self._reader = None, None
            if did_disconnect:
                self.packets_received.put_nowait(
                    Airtouch5ConnectionStateChange.DISCONNECTED
                )

    async def _read_packets(self):
        """
        Continuously read packets from the socket and put them in the queue.
        If we detect the socket has died, disconnect it
        """
        reader = self._reader
        if reader is None:
            raise Exception("Reader is None")

        try:
            while reader.at_eof() == False:
                read = await reader.read(1024)
                packets = self._packet_reader.read(read)
                for packet in packets:
                    self.packets_received.put_nowait(packet)
        except Exception as e:
            _LOGGER.error(f"Exception in reader task: {e}")

        # If we've finished reading for some reason, we should disconnect
        # Clear our task first so we don't get cancelled
        self._reader_task = None
        await self.disconnect()

    async def send_packet(self, packet: DataPacket):
        """
        Send the given packet to the airtouch 5.
        Throws if we aren't connected or if there is a connection issue
        """
        writer = self._writer
        if writer is None:
            raise Exception("Writer is None")

        _LOGGER.debug(f"Sending packet {packet}")
        try:
            writer.write(self._encoder.encode(packet))
            await writer.drain()
        except Exception as e:
            _LOGGER.error(f"Exception when sending packet: {e}")
            await self.disconnect()
            raise e
