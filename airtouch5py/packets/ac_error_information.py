from airtouch5py.packets.datapacket import Data


class AcErrorInformationData(Data):
    ac_number: int
    error_info: str
