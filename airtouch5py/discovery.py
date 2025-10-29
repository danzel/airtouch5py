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


class AirtouchDiscovery:
    DISCOVERY_PORT = 49005
    DISCOVERY_MESSAGE = "::REQUEST-POLYAIRE-AIRTOUCH-DEVICE-INFO:;"
    TIMEOUT = 3  # seconds

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

            return AirtouchDevice(*parts)
        except Exception as e:
            _LOGGER.error(f"❌ Failed to parse response: {e}")
            return None


    async def discover_airtouch_devices_broadcast(self, ip="255.255.255.255") -> list[AirtouchDevice]:

        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)  # non-blocking mode
        sock.bind(("", self.DISCOVERY_PORT))  # bind to receive responses on this port


        # Send packet
        loop = asyncio.get_running_loop()


        await loop.sock_sendto(sock, self.DISCOVERY_MESSAGE.encode('utf-8'), (ip, self.DISCOVERY_PORT))
        _LOGGER.info(f"Sent {len(self.DISCOVERY_MESSAGE)} bytes to {ip}:{self.DISCOVERY_PORT}")

        # (Optional) wait for a response

        my_ips = self._get_local_ips()
        _LOGGER.debug(f"Local IPs: {my_ips}")

        start_time = time.time()
        responses = []
        while time.time() - start_time < self.TIMEOUT:
            try:
                data, addr = await asyncio.wait_for(loop.sock_recvfrom(sock, 4096), timeout=0.5)
                sender_ip, _ = addr
                _LOGGER.info(f"✅ Received {len(data)} bytes from {addr}: {data}")
                if sender_ip in my_ips:
                    _LOGGER.info("(Ignoring response from self) {sender_ip}")
                    continue
                responses.append(self.parse_airtouch_response(data))
                start_time = time.time()  # reset timeout on each response
            except asyncio.TimeoutError:
                # No data within timeout window, continue waiting
                continue
        sock.close()
        return responses

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
