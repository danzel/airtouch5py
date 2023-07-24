import asyncio
import logging
import sys
from pprint import pprint

from airtouch5py.airtouch5_client import Airtouch5Client, Airtouch5ConnectionStateChange
from airtouch5py.airtouch5_simple_client import Airtouch5SimpleClient
from airtouch5py.packets.ac_ability import AcAbilityData
from airtouch5py.packets.ac_error_information import AcErrorInformationData
from airtouch5py.packets.ac_status import AcStatusData
from airtouch5py.packets.console_version import ConsoleVersionData
from airtouch5py.packets.datapacket import DataPacket
from airtouch5py.packets.zone_control import ZoneControlData
from airtouch5py.packets.zone_name import ZoneNameData
from airtouch5py.packets.zone_status import ZoneStatusData


def print_packet(packet: DataPacket):
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


async def main(ip: str):
    logger = logging.getLogger("airtouch5pytest")
    client = Airtouch5SimpleClient(ip)

    print("Testing connection")
    try:
        await client.test_connection()
        print("Succeeded")
    except Exception as e:
        print(f"Failed: {e}")
        return

    print("Connecting...")
    try:
        await client.connect_and_stay_connected()
    except Exception as e:
        print(f"Failed: {e}")
        return
    print(f"Connected, we have {len(client.zones)} zones and {len(client.ac)} acs")

    client.connection_callbacks.append(
        lambda x: print(f"Connection state changed to {x}")
    )
    client.message_callbacks.append(print_packet)

    await client.send_packet(client.data_packet_factory.zone_status_request())
    await client.send_packet(client.data_packet_factory.ac_status_request())

    await asyncio.sleep(999)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
