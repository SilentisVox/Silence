from core.CommandHandler import CommandHandler
from core.SilentServer   import SilentServer
from core.HttpServer     import HTTPServer

import core.TextAssets
import argparse

def main() -> None:
        core.TextAssets.cursor_off()
        core.TextAssets.print_banner()
        core.TextAssets.cursor_on()

        parser                          = argparse.ArgumentParser()
        parser.add_argument("-c", type=str, help="Callback address")
        parser.add_argument("-p", type=str, help="TCP Handler port (Default 4443)")
        parser.add_argument("-l", type=str, help="HTTP Stager port (Default 8080)")
        args                            = parser.parse_args()

        if not args.c:
                core.TextAssets.print_debug()
                return

        if not args.l:
                args.l                  = 4443

        if not args.p:
                args.p                  = 8080

        core.TextAssets.print_info("Starting services")
        core.TextAssets.print_info("Welcome to the silence shell!") 
        core.TextAssets.print_info("Please type 'help' for more options")

        silent_server                   = SilentServer(args.c, args.l)
        silent_server.initialize_server()
        
        http_server                     = HTTPServer(args.c, args.p, args.l)
        http_server.initialize_server()

        core.TextAssets.print_services(args.l, args.p)

        command_handler                 = CommandHandler(
                silent_server,
                http_server,
        )

        command_handler.generate()

        try:
                while True:
                        user_input      = input(core.TextAssets.prompt())
                        command_handler.handle_input(user_input)
        except KeyboardInterrupt:
                pass
        except Exception as exception:
                print(exception)

        if silent_server.listener:
                silent_server.shutdown()

        for client in silent_server.clients:
                client.client.close()

        if http_server.listener:
                http_server.shutdown()

        print()

if __name__ == "__main__":
        main()