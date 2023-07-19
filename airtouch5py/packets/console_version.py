from airtouch5py.packets.datapacket import Data


class ConsoleVersionData(Data):
    has_update: bool
    version: str
