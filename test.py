import asyncio
import sys
from pprint import pprint

from airtouch5py.airtouch5client import Airtouch5Client
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_name import ZoneNameRequestData


async def main(ip: str):
    client = Airtouch5Client(ip)
    print("Connecting...")
    await client.connect()
    await client.send_packet(DataPacket(0x90B0, 0x42, ZoneNameRequestData(None)))
    while True:
        packet = await client.packets_received.get()
        pprint(packet)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
