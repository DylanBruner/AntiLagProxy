def scrapeASCII(data: bytes) -> str:
    return "".join([chr(i) for i in data if i < 128])

def packVarInt(i: int) -> bytes:
    if i < 0: raise ValueError("Cannot pack negative integer")
    if i == 0: return b'\x00'
    b = []
    while i > 0:
        b.append(i & 0x7F)
        i >>= 7
    b.reverse()
    for i in range(len(b) - 1):
        b[i] |= 0x80
    return bytes(b)