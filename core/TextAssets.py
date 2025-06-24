import sys
import time

RED                                     = "\033[38;2;220;0;0m"
YELLOW                                  = "\033[38;2;227;176;0m"
GREEN                                   = "\033[38;2;90;220;100m"
BLUE                                    = "\033[38;2;100;180;230m"
GRAY                                    = "\033[38;2;80;80;80m"
UNDER                                   = "\001\033[4m\002"
END                                     = "\033[0m"

def format_banner():
        banner                          = """
    ┌─┐┬ ┬  ┌─┐┌┐┌┌─┐┌─┐
    └─┐│ │  ├- ││││  ├- 
    └─┘┴ ┴─┘└─┘┘└┘└─┘└─┘
"""

        banner                          = banner.split("\n")[:-1]
        colors                          = [255, 255, 207, 159]
        final                           = []

        for index, line in enumerate(banner):
                color_line              = f"\033[38;2;{colors[index]};0;0m{line}\033[0m"
                final.append(color_line)

        return "\n".join(final)

def type_effect(text):
        for i in text:
                sys.stdout.write(f'\033[38;2;20;20;20m{i}\033[0m')
                sys.stdout.flush()
                time.sleep(0.02)
                sys.stdout.write(f'\b\033[38;2;80;40;40m{i}\033[0m')
                sys.stdout.flush()
                time.sleep(0.02)
                sys.stdout.write(f'\b\033[38;2;207;0;0m{i}\033[0m')
                sys.stdout.flush()
                time.sleep(0.06)
                sys.stdout.write(f'\b{i}')

def print_banner():
        print(format_banner())
        print("                ", end="")
        type_effect("Descends")
        print("\n")

def print_info(text):
        print(f"{BLUE}[*]{END} {text}.")

def print_debug():
        print(f"{YELLOW}[Debug]{END} Local host IP not provided. (-c IP)")

def prompt():
        return f"{UNDER}Silence{END}> "

def shell():
        return f"{RED}[Shell]{END}"

def print_success():
        print(f"{GREEN}[!] Success!{END}")

def make_red(string):
        return RED + string + END

def make_yellow(string):
        return YELLOW + string + END

def make_green(string):
        return GREEN + string + END

def make_blue(string):
        return BLUE + string + END

def make_gray(string):
        return GRAY + string + END

def cursor_on():
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

def cursor_off():
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

def print_client(client):
        shelly                          = shell()
        client_id                       = client.client_id
        client_address                  = client.client_addr

        print(f"\r{shelly} {client_id} → {make_red(client_address)}")
        print(prompt(), end="", flush=True)
        
def print_clients(clients):
        print()
        print("Client ID       IP Address       OS Type  User       Status")
        print("--------------  ---------------  -------  ---------- ------")

        for client in clients:
                client_id     = client.client_id
                client_addr   = client.client_addr
                client_os     = client.client_os
                client_user   = client.client_user
                client_status = client.client_status

                if len(client_user) > 10:
                        client_user = client_user[:7] + "..."

                if client_status == "Active":
                        client_status = make_green(client_status)

                else:
                        client_status = make_red(client_status)

                print(f"{client_id}  {client_addr}{' ' * (15 - len(client_addr))}  {client_os}{' ' * (7 - len(client_os))}  {client_user}{' ' * (10 - len(client_user))} {client_status}")

        print()

def print_lost_client(client, with_prompt):
        shelly                          = shell()
        client_id                       = client.client_id
        lost                            = make_red("Lost")

        print(f"\r{shelly} {client_id} : Session {lost}", flush=True)
        
        if with_prompt:
                print(prompt(), flush=True, end="")

def print_jobs(jobs):
        print()
        print("Job          Port   Status")
        print("-----------  -----  --------")

        for job in jobs:
                if job[2]:
                        status          = make_green("Active")
                else:
                        status          = make_red("Inactive")

                print(f"{job[0]}  {job[1]}{' ' * (5 - len(job[1]))}  {status}")

        print()

def print_services(server, http):
        print()
        indicator                       = make_red("[+]")
        server_port                     = make_red(f"[{server}]")
        http_port                       = make_red(f"[{http}]")

        print(f"{indicator} TCP Handler {server_port}")
        print(f"{indicator} HTTP Stager {http_port}")
        print()

def get_help():
        print("""
        \r Command       Description
        \r ------------  ---------------------------------------------
        \r
        \r shell    [+]  Begins communication with a specified client.
        \r
        \r sessions      Displays current sessions avaialable.
        \r
        \r generate      Generates a 1-stop-shop payload that creates
        \r               a reverse shell with the current settings.
        \r
        \r jobs          Displays current services running.
        \r
        \r start    [+]  Starts a given service [handler|listener],
        \r               with given args [callback_ip|callback_port]
        \r
        \r stop     [+]  Stops a given service [handler|listener].
        \r
        \r kill     [+]  Kills a connection with a specified client.
        \r
        \r help          Displays this menu.
        \r
        \r clear         Clears the terminal window.
        \r
        \r exit          Exits Silence.
        """)

def get_command_help(description):
        print(f"""
        \r Command Description
        \r ----------------------------------------------------------------------
           {description}""")