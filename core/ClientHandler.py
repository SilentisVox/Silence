import threading
import core.TextAssets

class ClientHandler:
        def __init__(self, client: object) -> None:
                self.client             = client
                self.connected          = True
                self.recv_thread        = None
                self.close_comm         = False

        def recvall(self) -> None:
                while self.connected:
                        if self.close_comm:
                                self.close_comm = False
                                return

                        data            = self.get_parts()

                        if not data:
                                continue

                        print(data, end="", flush=True)

                self.client.client_status = "Lost"
                core.TextAssets.print_lost_client(self.client, False)
                print("Press <ENTER> ...", end="", flush=True)

        def get_parts(self) -> str:
                data = ""
                while self.connected and not self.close_comm:
                        try:
                                part            = self.client.client.recv(1024).decode("utf-8", errors="replace")

                                if not part:
                                        raise Exception("Connection closed by remote host.")
                                        self.client.close()

                        except BlockingIOError:
                                continue
                        except:
                                self.connected = False
                                return

                        data           += part

                        if len(part) < 1024:
                                break

                return data

        def sendall(self) -> None:
                while self.connected:
                        try:
                                data    = input() + "\n"
                                self.client.client.send(data.encode())
                        except KeyboardInterrupt:
                                self.close_comm = True
                                print()
                                break
                        except:
                                return

        def begin_comm(self) -> bool:
                self.client.client.send(b"\n")
                self.recv_thread        = threading.Thread(
                        target          = self.recvall
                )
                self.recv_thread.start()
                self.sendall()
