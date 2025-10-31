from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from re import L
import socket
import time

_LOGGER = logging.getLogger(__name__)


@dataclass
class AirtouchDevice:
    # [IP],[ConsoleID],AirTouch5,[AirTouch ID],[Device Name]
    ip: str
    console_id: str
    model: str
    system_id: str
    name: str

    def __repr__(self) -> str:
        return f"AirtouchDevice(ip={self.ip}, console_id={self.console_id}, model={self.model}, system_id={self.system_id}, name={self.name})"

class AirtouchDiscoveryProtocol(asyncio.DatagramProtocol):
    """Async listener for Airtouch UDP discovery packets."""

    def __init__(self, my_ips, parse_func):
        self.my_ips = my_ips
        self.parse_func = parse_func

    def datagram_received(self, data, addr):
        sender_ip, _ = addr

        if sender_ip in self.my_ips:
            _LOGGER.debug(f"Ignoring self-response from {sender_ip}")
            return

        _LOGGER.info(f"✅ Received {len(data)} bytes from {addr}")
        self.parse_func(data)


    def error_received(self, exc):
        _LOGGER.warning(f"UDP socket error: {exc}")

    def connection_lost(self, exc):
        _LOGGER.info("UDP connection closed")

class AirtouchDiscovery:
    DISCOVERY_PORT = 49005
    DISCOVERY_MESSAGE = "::REQUEST-POLYAIRE-AIRTOUCH-DEVICE-INFO:;"
    TIMEOUT = 3  # seconds
    responses: list[AirtouchDevice]
    loop: asyncio.AbstractEventLoop
    my_ips: list[str]
    transport: asyncio.DatagramTransport

    def __init__(self):
        self.responses = []
        self.loop = asyncio.get_event_loop()
        self.my_ips = self._get_local_ips()

    async def establish_server(self):
       # Create UDP socket
        transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: AirtouchDiscoveryProtocol(self.my_ips, self.parse_airtouch_response),
            local_addr=("0.0.0.0", self.DISCOVERY_PORT),
            allow_broadcast=True
        )
        self.transport = transport

    async def close(self):
        """Cleanly close the UDP socket."""
        if self.transport:
            _LOGGER.debug("Closing AirtouchDiscovery UDP listener")
            self.transport.close()
            self.transport = None

    def parse_airtouch_response(self, raw_response: bytes) -> AirtouchDevice | None:
        """
        Parse an Airtouch discovery response line like:
        b'192.168.1.10,AT5N202502000000,AirTouch5,4300000,Upstairs'
        """
        try:
            decoded = raw_response.decode("utf-8").strip()
            parts = decoded.split(",")
            if len(parts) != 5:
                _LOGGER.info(f"⚠️ Unexpected response format: {decoded}")
                return None

            self.responses.append(AirtouchDevice(*parts))
        except Exception as e:
            _LOGGER.error(f"❌ Failed to parse response: {e}")
            return None


    async def discover(self, ip="255.255.255.255") -> list[AirtouchDevice]:
        try:
            # Broadcast discovery packet
            message = self.DISCOVERY_MESSAGE.encode('utf-8')
            self.transport.sendto(message, (ip, self.DISCOVERY_PORT))
            _LOGGER.info(f"Sent {len(self.DISCOVERY_MESSAGE)} bytes to {ip}:{self.DISCOVERY_PORT}")

            # Wait for TIMEOUT seconds to gather responses
            await asyncio.sleep(self.TIMEOUT)
        finally:
            self.transport.close()

        return self.responses

    def _get_local_ips(self):
        """Return a list of this machine's IP addresses."""
        ips = []
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # doesn’t actually send data
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            pass
        return list(set(ips))  # remove duplicates
