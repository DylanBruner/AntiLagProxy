import socket, threading, colorama

SERVER_TO_CLIENT = "client"
CLIENT_TO_SERVER = "server"
ON_DISCONNECT    = "disconnect"


socket.setdefaulttimeout(None)

class Connection(object):
    def __init__(self, conn: socket.socket, addr: tuple, redirAddr: tuple, routes: list, max_retries: int = 3):
        self.conn = conn
        self.addr = addr
        self.REDIR_TO = redirAddr

        self.routes = routes

        self.max_retries = max_retries

        self.client_to_server_inter = None
        self.server_to_client_inter = None

        for route in self.routes:
            if route[0] == "client":
                self.server_to_client_inter = route[1]
            elif route[0] == "server":
                self.client_to_server_inter = route[1]


        self.ServerSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.ServerSoc.connect(self.REDIR_TO)
        except Exception as e:
            print(f"{colorama.Fore.RED}Error connecting to {self.REDIR_TO[0]}:{self.REDIR_TO[1]} {colorama.Fore.RESET}")
            return
        # print(f"Connected to {self.REDIR_TO[0]}:{self.REDIR_TO[1]}")
    
    def _onDisconnect(self, soc: socket.socket, addr: tuple):
        soc.close()
        self.conn.close()
        self.ServerSoc.close()
        for route in self.routes:
            if route[0] == "disconnect":
                route[1](self.conn, self.addr)
    
    def _client_to_server(self, retries: int = 4):
        try:
            while True:
                # If socket is closed, break
                if self.conn.fileno() == -1 or self.ServerSoc.fileno() == -1: break

                data = self.conn.recv(8024)
                if self.client_to_server_inter != None:
                    data = self.client_to_server_inter(data, self.conn)
                if len(data) != 0 and self.ServerSoc.fileno() != -1:
                    self.ServerSoc.send(data)
        except ConnectionAbortedError as e:
            if retries < self.max_retries:
                print(f"{colorama.Fore.YELLOW}Retrying {self.addr[0]}:{self.addr[1]} -> {self.REDIR_TO[0]}:{self.REDIR_TO[1]} {colorama.Fore.RESET}")
                self._client_to_server(retries + 1)
            else: 
                # print(f"{colorama.Fore.RED}Connection aborted {self.addr[0]}:{self.addr[1]} -> {self.REDIR_TO[0]}:{self.REDIR_TO[1]} {colorama.Fore.RESET}")
                self._onDisconnect(self.conn, self.addr)

    def _server_to_client(self, retries: int = 4):
        try:
            while True:
                # If socket is closed, break
                if self.ServerSoc.fileno() == -1 or self.conn.fileno() == -1: break

                data = self.ServerSoc.recv(8024)
                if self.server_to_client_inter != None:
                    data = self.server_to_client_inter(data, self.conn)
                if len(data) != 0 and self.conn.fileno() != -1:
                    self.conn.send(data)
        except ConnectionAbortedError:
            if retries < self.max_retries:
                print(f"{colorama.Fore.YELLOW}Retrying {self.REDIR_TO[0]}:{self.REDIR_TO[1]} -> {self.addr[0]}:{self.addr[1]} {colorama.Fore.RESET}")
                self._server_to_client(retries + 1)
            else: 
                # print(f"{colorama.Fore.RED}Connection aborted {self.REDIR_TO[0]}:{self.REDIR_TO[1]} -> {self.addr[0]}:{self.addr[1]} {colorama.Fore.RESET}")
                self._onDisconnect(self.conn, self.addr)

    def run(self):
        print(f"{colorama.Fore.CYAN}Starting forwarder {self.addr[0]}:{self.addr[1]} -> {self.REDIR_TO[0]}:{self.REDIR_TO[1]} {colorama.Fore.RESET}")
        threading.Thread(target=self._client_to_server).start()
        threading.Thread(target=self._server_to_client).start()

class Server(object):
    def __init__(self, RECV_ADDR: tuple, REDIR_ADDR: tuple):
        self.RECV_ADDR = RECV_ADDR
        self.REDIR_ADDR = REDIR_ADDR

        self.connections = []
        self.routes      = []
    
    def route(self, name: str):
        def decorator(func):
            self.routes.append((name, func))
            return func
        return decorator

    def start(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.bind(self.RECV_ADDR)
        self.soc.listen(5)
        print(f"Listening on {self.RECV_ADDR[0]}:{self.RECV_ADDR[1]}")
        while True:
            conn, addr = self.soc.accept()
            # print(f"Recived connection from {addr[0]}:{addr[1]}")
            conec = Connection(conn, self.RECV_ADDR, self.REDIR_ADDR, self.routes)
            threading.Thread(target=conec.run).start()