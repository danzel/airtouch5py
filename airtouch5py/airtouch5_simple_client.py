import asyncio
import logging
from typing import Callable, TypeVar

from airtouch5py.airtouch5_client import Airtouch5Client, Airtouch5ConnectionStateChange
from airtouch5py.data_packet_factory import DataPacketFactory
from airtouch5py.packets.ac_ability import AcAbility, AcAbilityData
from airtouch5py.packets.ac_status import AcStatus, AcStatusData
from airtouch5py.packets.console_version import ConsoleVersionData
from airtouch5py.packets.datapacket import Data, DataPacket
from airtouch5py.packets.zone_name import ZoneName, ZoneNameData
from airtouch5py.packets.zone_status import ZoneStatusData, ZoneStatusZone

_LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


class Airtouch5SimpleClient:
    """
    A simple Airtouch5 client.

    Usage:
    Call connect_and_stay_connected().
    Add listeners to *_callbacks
    The Airtouch5 will automatically send out updates to zone status and ac status as they happen.
    """

    data_packet_factory: DataPacketFactory

    # Populated after connect_and_stay_connected
    ac: list[AcAbility]
    # Populated after connect_and_stay_connected
    zones: list[ZoneName]
    # Populated after connect_and_stay_connected
    console_version: str
    # Populated after connect_and_stay_connected
    latest_ac_status: dict[int, AcStatus]
    # Populated after connect_and_stay_connected
    latest_zone_status: dict[int, ZoneStatusZone]

    connection_state_callbacks: list[Callable[[Airtouch5ConnectionStateChange], None]]
    data_packet_callbacks: list[Callable[[DataPacket], None]]
    ac_status_callbacks: list[Callable[[dict[int, AcStatus]], None]]
    zone_status_callbacks: list[Callable[[dict[int, ZoneStatusZone]], None]]

    _client: Airtouch5Client
    _connection_task: asyncio.Task[None] | None

    def __init__(self, ip: str):
        self.ip = ip
        self._client = Airtouch5Client(ip)
        self.data_packet_factory = DataPacketFactory()

        self.ac = []
        self.zones = []
        self.console_version = ""

        self.connection_state_callbacks = []
        self.data_packet_callbacks = []
        self.ac_status_callbacks = []
        self.zone_status_callbacks = []

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
        Gets the AC ability and zone names, initial zone status and ac status, and then waits for updates.
        Throws if we fail to make the initial connection.
        """
        await self._client.connect()

        # Get the ac abilities
        await self._client.send_packet(self.data_packet_factory.ac_ability_request())
        self.ac = (await self._wait_for_packet_or_throw(AcAbilityData)).ac_ability

        # Get the zone names
        await self._client.send_packet(self.data_packet_factory.zone_name_request())
        self.zones = (await self._wait_for_packet_or_throw(ZoneNameData)).zone_names

        # Get the version
        await self._client.send_packet(
            self.data_packet_factory.console_version_request()
        )
        self.console_version = (
            await self._wait_for_packet_or_throw(ConsoleVersionData)
        ).version

        # Get the initial zone status
        await self._client.send_packet(self.data_packet_factory.zone_status_request())
        self.latest_zone_status = {
            zone.zone_number: zone
            for zone in (await self._wait_for_packet_or_throw(ZoneStatusData)).zones
        }

        # Get the initial ac status
        await self._client.send_packet(self.data_packet_factory.ac_status_request())
        self.latest_ac_status = {
            ac.ac_number: ac
            for ac in (await self._wait_for_packet_or_throw(AcStatusData)).ac_status
        }

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
                    raise Exception(f"Disconnected while waiting for a {packet_type}")
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
            # Wait for a packet, or timeout after 5 minutes
            packet: DataPacket | Airtouch5ConnectionStateChange
            try:
                packet = await asyncio.wait_for(
                    self._client.packets_received.get(), 5 * 60
                )
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout waiting for packet, reconnecting")
                await self._client.disconnect()
                # disconnect pushes a DISCONNECTED message in to the queue, so we'll reconnect
                continue

            _LOGGER.debug(f"maintain Received packet {packet}")
            if packet is Airtouch5ConnectionStateChange.DISCONNECTED:
                [cb(packet) for cb in self.connection_state_callbacks]
                _LOGGER.warning("Disconnected from Airtouch 5, reconnecting")
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
                [cb(packet) for cb in self.connection_state_callbacks]
            elif isinstance(packet, DataPacket):
                [cb(packet) for cb in self.data_packet_callbacks]
                if isinstance(packet.data, ZoneStatusData):
                    # convert the list to a dict, store it and broadcast it
                    self.latest_zone_status = {
                        zone.zone_number: zone for zone in packet.data.zones
                    }
                    [cb(self.latest_zone_status) for cb in self.zone_status_callbacks]
                if isinstance(packet.data, AcStatusData):
                    # convert the list to a dict, store it and broadcast it
                    self.latest_ac_status = {
                        ac.ac_number: ac for ac in packet.data.ac_status
                    }
                    [cb(self.latest_ac_status) for cb in self.ac_status_callbacks]
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
