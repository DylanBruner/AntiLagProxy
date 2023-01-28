import typing, utils, quarry

def unMutilateString(s: str) -> str: # Fix some weird af bug when decoding strings
    return "".join([i for i in s if i in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._"])

def isJoinPacket(data: bytes) -> tuple[bool, str]:
    """
    Returns a tuple of (True/False, version/None)
    """
    version = getPacketVersion(data)

    if version == '1.8.9':
        return ('\\x14\\x00/\\x0e' in str(data) or '\\x19\\x00' in str(data), version)
    
    return (False, None)

def getUsername(data: bytes) -> str:
    jp, version = isJoinPacket(data)
    if not jp: raise ValueError("Not a join packet")

    if version == '1.8.9':
        return unMutilateString(utils.scrapeASCII(data.split(b'\x00')[-1]).strip())

def getHostname(data: bytes) -> str:
    jp, version = isJoinPacket(data)
    if not jp: raise ValueError("Not a join packet")

    if version == '1.8.9':
        return unMutilateString(utils.scrapeASCII(data.split(b'\x00')[1]).replace("/", "").strip())

def patchHostname(data: bytes, hosts: list[str], to_host: str) -> bytes:
    jp, version = isJoinPacket(data)
    # if not jp: raise ValueError("Not a join packet")

    if version == '1.8.9':
        for host in hosts:
            if host in str(data):
                data = data.replace(host.encode(), to_host.encode())
                break
    return data

def getPacketVersion(data: bytes) -> str:
    # Only works on join packets right now
    if '\\x14' in str(data) or '\\x19' in str(data): 
        return '1.8.9'
    elif 0:
        return '1.19.2'