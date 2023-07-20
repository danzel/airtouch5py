from airtouch5py.packets.datapacket import Data


class ConsoleVersionRequestData(Data):
    pass


class ConsoleVersionData(Data):
    has_update: bool
    version: str

    def __init__(self, has_update: bool, version: str):
        self.has_update = has_update
        self.version = version
