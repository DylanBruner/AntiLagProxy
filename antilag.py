import tcpproxy, socket, colorama, versions, time


proxy = tcpproxy.Server(("0.0.0.0", 8191), ("mc.hypixel.net", 25565))
# proxy = tcpproxy.Server(("0.0.0.0", 8191), ("top.mc-complex.com", 25565))

whitelisted_users = ["Frost19", "OhGaming_"]
proxy_host        = "ohgamingaa.net"

# IP:PORT -> username
connected_players = {}
packet_counter    = {}

# ANTI-LAG Config
MAX_PACKETS_PER_SECOND = 225

# ANTI-LAG Trackers
packetsSent = {} # IP:PORT -> {packet_count, start_time}

# ===================

def adjustIP(ip: str) -> str:
    if ip in ['127.0.0.1', 'localhost']:
        return '0.0.0.0'
    return ip

def onPacket(conn: socket.socket):
    ip = adjustIP(conn.getpeername()[0])
    if ip not in packetsSent:
        packetsSent[ip] = {"packet_count": 0, "start_time": time.time()}
    
    packetsSent[ip]["packet_count"] += 1

    if packetsSent[ip]["packet_count"] > MAX_PACKETS_PER_SECOND and time.time() - packetsSent[ip]["start_time"] < 1:
        username = connected_players.get(ip, ip)
        print(f"{colorama.Fore.YELLOW}[INFO::ANTI-LAG] {username} is sending too many packets, slowing them down {colorama.Fore.RESET}")
        time.sleep(1)
    
    if time.time() - packetsSent[ip]["start_time"] > 1:
        packetsSent[ip]["packet_count"] = 0
        packetsSent[ip]["start_time"] = time.time()
        

@proxy.route(tcpproxy.ON_DISCONNECT)
def on_disconnect(conn: socket.socket, addr: tuple):
    ip = adjustIP(addr[0])
    username = connected_players.get(ip, None)
    if username != None:
        print(f"{colorama.Fore.RED}[INFO] {username} disconnected {colorama.Fore.RESET}")
        # Remove the ip from connected_players if it's in it
        if ip in connected_players:
            del connected_players[ip]
            if ip in packet_counter:
                del packet_counter[ip]
    else:
        print(f"{colorama.Fore.RED}[INFO] Unknown player disconnected {colorama.Fore.RESET}")

@proxy.route("client")
def client(data: bytes, conn: socket.socket):
    if len(data) < 0 or data == b'': return data
    try:
        packet_counter[adjustIP(conn.getpeername()[0])] = packet_counter.get(adjustIP(conn.getpeername()[0]), 0) + 1

        # onPacket(conn) # For packet rate limiting
        # ^ shouldn't need this as it limits packets from the server -> client

    except OSError as e:
        print(f"{colorama.Fore.RED}[ERROR] {e} {colorama.Fore.RESET}")

    return data

@proxy.route("server")
def server(data: bytes, conn: socket.socket):
    if len(data) < 0 or data == b'': return data
    if not conn: return data

    try:
        packet_counter[adjustIP(conn.getpeername()[0])] = packet_counter.get(adjustIP(conn.getpeername()[0]), 0) + 1

        if packet_counter[adjustIP(conn.getpeername()[0])] > 50 and adjustIP(conn.getpeername()[0]) not in connected_players:
            print(f"{colorama.Fore.RED}[INFO::KICK] {adjustIP(conn.getpeername()[0])} wasn't registered {colorama.Fore.RESET}")
            conn.close()
            del packet_counter[adjustIP(conn.getpeername()[0])]
            return

        # pretend that were connected to the real server not a proxy
        data = data.replace(proxy_host.encode(), proxy.REDIR_ADDR[0].encode())
        # print(data)

        if versions.isJoinPacket(data)[0]:
            hostname = versions.getHostname(data)
            username = versions.getUsername(data)
            if username.strip() == '' or hostname.strip() == '': return data

            # if the ip is 127.0.0.1 or localhost set it to 0.0.0.0
            connected_players[adjustIP(conn.getpeername()[0])] = username

            print(f"{colorama.Fore.GREEN}[INFO] New connection from {username} through {hostname} ({colorama.Fore.RESET}whitelisted={str(username in whitelisted_users).replace('False', colorama.Fore.RED+'no').replace('True', colorama.Fore.CYAN+'yes')+colorama.Fore.GREEN}) {colorama.Fore.RESET}")
            if username not in whitelisted_users:
                print(f"{colorama.Fore.RED}[INFO] Kicked {username} {colorama.Fore.RESET}")
                conn.close()


        onPacket(conn) # For packet rate limiting
    except OSError as e:
        print(f"{colorama.Fore.RED}[ERROR] {e} {colorama.Fore.RESET}")
        
    return data

proxy.start()