import asyncio
import logging
from pprint import pprint

from airtouch5py.airtouch5client import Airtouch5Client, Airtouch5ConnectionStateChange
from airtouch5py.packets.ac_ability import AcAbilityData
from airtouch5py.packets.ac_error_information import AcErrorInformationData
from airtouch5py.packets.ac_status import AcStatusData
from airtouch5py.packets.console_version import ConsoleVersionData
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_control import ZoneControlData
from airtouch5py.packets.zone_name import ZoneNameData
from airtouch5py.packets.zone_status import ZoneStatusData


async def main(ip: str):
    logger = logging.getLogger("airtouch5pytest")
    client = Airtouch5Client(ip)
    print("Connecting...")
    client.connect()
    print("Waiting for connection...")

    packet = await client.packets_received.get()
    if packet is not Airtouch5ConnectionStateChange.CONNECTED:
        logger.error("Didn't receive connected as our first packet from the queue")
        return
    print("Connected")

    await client.send_packet(client.data_packet_factory.zone_name_request())
    while True:
        packet = await client.packets_received.get()
        match packet:
            case Airtouch5ConnectionStateChange.DISCONNECTED:
                logger.info("Disconnected")
            case Airtouch5ConnectionStateChange.CONNECTED:
                logger.info("Connected")
            case DataPacket():
                match packet.data:
                    case ZoneControlData():
                        print(f"Received {len(packet.data.zones)} zones data")
                        pprint(packet.data.zones)

                    case ZoneStatusData():
                        print(f"Received {len(packet.data.zones)} zones status")
                        pprint(packet.data.zones)

                    case AcStatusData():
                        print(f"Received {len(packet.data.ac_status)} ac status")
                        pprint(packet.data.ac_status)

                    case AcAbilityData():
                        print(f"Received {len(packet.data.ac_ability)} ac ability")
                        pprint(packet.data.ac_ability)

                    case AcErrorInformationData():
                        print(
                            f"Received ac error information {packet.data.ac_number} {packet.data.error_info}"
                        )

                    case ZoneNameData():
                        print(f"Received {len(packet.data.zone_names)} zones names")
                        pprint(packet.data.zone_names)

                    case ConsoleVersionData():
                        print(
                            f"Received console version. has update {packet.data.has_update}, version {packet.data.version}"
                        )

                    case _:
                        print(f"Received unknown packet {packet.data}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
