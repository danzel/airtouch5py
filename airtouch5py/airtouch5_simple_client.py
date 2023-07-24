import asyncio
import logging
from typing import Callable, TypeVar

from airtouch5py.airtouch5_client import Airtouch5Client, Airtouch5ConnectionStateChange
from airtouch5py.data_packet_factory import DataPacketFactory
from airtouch5py.packets.ac_ability import AcAbility, AcAbilityData
from airtouch5py.packets.console_version import ConsoleVersionData
from airtouch5py.packets.datapacket import Data, DataPacket
from airtouch5py.packets.zone_name import ZoneName, ZoneNameData

_LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


class Airtouch5SimpleClient:
    """
    A simple Airtouch5 client.

    Call connect_and_stay_connected().
    Add listeners to {TODO}
    Send initial requests for zone status and ac status (These will be updated as they change in the future, but you should do an initial request to get initial state)
    """

    data_packet_factory: DataPacketFactory

    # Populated after connect_and_stay_connected
    ac: list[AcAbility]
    # Populated after connect_and_stay_connected
    zones: list[ZoneName]

    connection_callbacks: list[Callable[[Airtouch5ConnectionStateChange], None]]
    message_callbacks: list[Callable[[DataPacket], None]]

    _client: Airtouch5Client
    _connection_task: asyncio.Task[None] | None

    def __init__(self, ip: str):
        self.ip = ip
        self._client = Airtouch5Client(ip)
        self.data_packet_factory = DataPacketFactory()
        self.ac = []
        self.zones = []
        self.connection_callbacks = []
        self.message_callbacks = []

    async def test_connection(self) -> None:
        """
        Connect, verify the connection, disconnect.
        Throws if something goes wrong.
        """
        await self._client.connect()

        try:
            # Send a console version request to verify this is an Airtouch 5 console
            await self._client.send_packet(
                self.data_packet_factory.console_version_request()
            )

            # Wait for the response
            start_wait = asyncio.get_running_loop().time()
            got_response = False
            while (
                asyncio.get_running_loop().time() - start_wait < 5 and not got_response
            ):
                packet = await asyncio.wait_for(self._client.packets_received.get(), 5)
                if isinstance(packet, DataPacket) and isinstance(
                    packet.data, ConsoleVersionData
                ):
                    got_response = True
                    break

            if not got_response:
                raise Exception("Didn't receive a console version response")
        finally:
            await self._client.disconnect()

    async def connect_and_stay_connected(self) -> None:
        """
        Connect, and reconnect if we disconnect.
        Gets the AC ability and zone names, and then waits for updates.
        Throws if we fail to make the initial connection.
        """
        await self._client.connect()

        # Get the ac abilities
        await self._client.send_packet(self.data_packet_factory.ac_ability_request())
        self.ac = (await self._wait_for_packet_or_throw(AcAbilityData)).ac_ability

        # Get the zone names
        await self._client.send_packet(self.data_packet_factory.zone_name_request())
        self.zones = (await self._wait_for_packet_or_throw(ZoneNameData)).zone_names

        # Start up the connection/reader task
        self._connection_task = asyncio.create_task(self._maintain_connection())

    async def _wait_for_packet_or_throw(self, packet_type: type[T]) -> T:
        """
        Wait 5 seconds for a packet of the given type, or throw if we disconnect or timeout.
        """

        async def _read_packets_until_match() -> T:
            while True:
                packet = await self._client.packets_received.get()
                if packet is Airtouch5ConnectionStateChange.DISCONNECTED:
                    raise Exception("Disconnected")
                if isinstance(packet, DataPacket) and isinstance(
                    packet.data, packet_type
                ):
                    return packet.data

        return await asyncio.wait_for(_read_packets_until_match(), 5)

    async def _maintain_connection(self) -> None:
        """
        Read messages off the queue, reconnecting if we disconnect.
        Calls the matching callbacks.
        """
        while True:
            packet = await self._client.packets_received.get()
            print(f"maintain Received packet {packet}")
            if packet is Airtouch5ConnectionStateChange.DISCONNECTED:
                [cb(packet) for cb in self.connection_callbacks]
                _LOGGER.warn("Disconnected from Airtouch 5, reconnecting")
                while True:
                    try:
                        await self._client.connect()
                        break
                    except Exception as e:
                        _LOGGER.error(
                            f"Failed to reconnect: {e}, will reconnect in 5 seconds"
                        )
                        await asyncio.sleep(5)
            elif packet is Airtouch5ConnectionStateChange.CONNECTED:
                [cb(packet) for cb in self.connection_callbacks]
            elif isinstance(packet, DataPacket):
                [cb(packet) for cb in self.message_callbacks]
            else:
                _LOGGER.error(f"Received unknown packet type {packet}")

    async def send_packet(self, packet: DataPacket) -> None:
        """
        Send a packet.
        """
        await self._client.send_packet(packet)

    async def disconnect(self) -> None:
        """
        Disconnect, and stop reconnecting.
        """
        if self._connection_task is not None:
            self._connection_task.cancel()
        await self._client.disconnect()
