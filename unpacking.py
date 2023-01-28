from struct import pack, unpack, unpack_from, calcsize

def varint_pack(d):
    o = b''
    while True:
        b = d & 0x7F
        d >>= 7
        o += pack("B", b | (0x80 if d > 0 else 0))
        if d == 0:
            break
    return o
def varint_unpack(s):
    d, l = 0, 0
    length = len(s)
    if length > 5:
        length = 5
    for i in range(length):
        l += 1
        b = s[i]
        d |= (b & 0x7F) << 7 * i
        if not b & 0x80:
            break
    return (d, s[l:])

# Lots of packets have a varint in front of a value, saying how long it is.
def data_pack(data):
    return varint_pack(len(data)) + data
def data_unpack(bytes):
    length, bytes = varint_unpack(bytes)
    return bytes[:length], bytes[length:]

# Same as data_*, but encoding and decoding strings, because I'm lazy.
def string_pack(string):
    return data_pack(string.encode())
def string_unpack(bytes):
    string, rest = data_unpack(bytes)
    return string.decode(), rest

# Same as struct.unpack_from, but returns remaining data.
def struct_unpack(format, struct):
    data = unpack_from(format, struct)
    rest = struct[calcsize(format):]
    return data, rest

def GetPacketId(packet):
    packet = data_unpack(packet)[0]
    packid, packet = varint_unpack(packet)
    packid = str(hex(packid))
    
    return packid

def GetPacketData(packet):
    packet = data_unpack(packet)[0]
    packid, packet = varint_unpack(packet)
    packid = str(hex(packid))
    
    return packet