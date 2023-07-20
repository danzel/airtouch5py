from airtouch5py.packets.datapacket import Data


class AcErrorInformationRequestData(Data):
    ac_number: int

    def __init__(self, ac_number: int):
        self.ac_number = ac_number


class AcErrorInformationData(Data):
    ac_number: int
    error_info: str

    def __init__(self, ac_number: int, error_info: str):
        self.ac_number = ac_number
        self.error_info = error_info
