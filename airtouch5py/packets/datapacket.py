class Data:
    pass


class DataPacket:
    address: int
    message_id: int
    data: Data

    def __init__(self, address: int, message_id: int, data: Data):
        self.address = address
        self.message_id = message_id
        self.data = data
