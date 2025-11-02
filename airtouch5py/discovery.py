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

    def __init__(self):
        self.responses: list[AirtouchDevice] = []
        self.loop = asyncio.get_running_loop()
        self.my_ips = self._get_local_ips()
        self.transport: asyncio.DatagramTransport | None = None

    async def _ensure_server(self):
        """Make sure transport is ready before sending packets."""
        if self.transport is None:
            await self.establish_server()
        self.responses = []  # reset every discovery attempt

    async def establish_server(self):
       # Create UDP socket
        transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: AirtouchDiscoveryProtocol(self.my_ips, self.parse_airtouch_response),
            local_addr=("0.0.0.0", self.DISCOVERY_PORT),
            allow_broadcast=True,
            reuse_port=True,  # ✅ allow multiple listeners (important for HA)
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

    async def discover_by_ip(self, ip: str) -> AirtouchDevice | None:
        await self._ensure_server()

        message = self.DISCOVERY_MESSAGE.encode('utf-8')
        self.transport.sendto(message, (ip, self.DISCOVERY_PORT))
        _LOGGER.info(f"Sent {len(self.DISCOVERY_MESSAGE)} bytes to {ip}:{self.DISCOVERY_PORT}")
        await asyncio.sleep(self.TIMEOUT)
        return self.responses[0] if self.responses else None



    async def discover(self, ip="255.255.255.255") -> list[AirtouchDevice]:
        await self._ensure_server()

        message = self.DISCOVERY_MESSAGE.encode("utf-8")
        self.transport.sendto(message, (ip, self.DISCOVERY_PORT))
        _LOGGER.info(f"Sent {len(self.DISCOVERY_MESSAGE)} bytes to {ip}:{self.DISCOVERY_PORT}")


        await asyncio.sleep(self.TIMEOUT)
        return list(self.responses)

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
