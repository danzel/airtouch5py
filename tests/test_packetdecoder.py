from airtouch5py.datapacket import DataPacket
from airtouch5py.packetdecoder import PacketDecoder

"""
Decode the zone control message as given in the protocol documentation
"""
async def test_decode_zonecontrol_example():
    decoder = PacketDecoder()
    #TODO: Add CRC bytes
    data = b'\x55\x55\x55\xAA\x80\xB0\x0F\xC0\x00\x0C\x20\x00\x00\x00\x00\x04\x00\x01\x01\x02\xFF\x00'
    packet: DataPacket = decoder.direct_decode(data)