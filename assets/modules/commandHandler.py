import os
from time import sleep as sl
import math
import pyfiglet
import sqlite3
import subprocess
import types
import random
import importlib
import psutil
import time
from modules.authSys import set_lockout, new_alias, remove_alias, add_notice, rem_notice
from modules.chronicle_engine import chronicle_log, clean_slate
import colorama
from modules.dbUtils import LDBConn
from colorama import Fore, Back, Style
from modules.animations import access_anim
from modules.access import access, search, db_deactive, update_dataset, export_scp
from modules.usrActions import main as usractions
from ESDS import run_esds
from cryptography.fernet import Fernet
colorama.init(autoreset=True)
variables = dict()


figlet = pyfiglet.figlet_format("SCP", font="doh") + Fore.LIGHTCYAN_EX + pyfiglet.figlet_format("Foundation", font="standard")
figlet = str(figlet).replace("\n", "\n\t\t\t")

available_cmds = f"""Current available commands:
{Fore.CYAN}help{Fore.GREEN} - Displays this list
{Fore.CYAN}lockdown{Fore.GREEN} - Initiates the emergency lockout system on the current frontend
{Fore.CYAN}access <SCP-No>{Fore.GREEN} - Access mentioned SCP. If entered 'random', a random file will be shown
{Fore.CYAN}search <keyword>{Fore.GREEN} - Search for SCPs containing the keyword in their title or text
{Fore.CYAN}logout{Fore.GREEN} - Logs out from current session, does not close the program
{Fore.CYAN}usredit{Fore.GREEN} - Inititates the user control interface
{Fore.CYAN}evaluate{Fore.GREEN} - Evaluates a scientific expression
{Fore.CYAN}update{Fore.GREEN} - Updates database
{Fore.CYAN}notice [subcommand]{Fore.GREEN} - Notice Actions
{Fore.CYAN}export_scp <SCP-No> <file_format>{Fore.GREEN} - Export mentioned SCP to the given file format
{Fore.CYAN}encrypt <file_path>{Fore.GREEN} - Encryptes mentioned file with a randomly generated key
{Fore.CYAN}decrypt <file_path> <key>{Fore.GREEN} - Decryptes mentioned file with the specified key
{Fore.CYAN}uptime{Fore.GREEN} - Shows system uptime
{Fore.CYAN}log <msg>{Fore.GREEN} - Manual log, logs the message
{Fore.CYAN}trace <address>{Fore.GREEN} - Traces the route to the specified network address
{Fore.CYAN}clean{Fore.GREEN} - Removes current activity logs
{Fore.CYAN}vars{Fore.GREEN} - Shows all defined variables and their value -- For Debugging
{Fore.CYAN}alias [subcommand]{Fore.GREEN} - Alias actions
{Fore.CYAN}inco{Fore.GREEN} - Enables/Disables INCOGNITO mode
{Fore.CYAN}cls/clear{Fore.GREEN} - Clear terminal
{Fore.CYAN}esds{Fore.RED} - WARNING! Do not use! Initiates Emergency Self Destruct System!
{Fore.CYAN}quit/exit{Fore.GREEN} - Quits the terminal"""

ccs = {}

cmd_help = {
    "help": " help [cmd] - Display a detailed help text about [cmd](optional), if not entered displays the normal help text",
    "resetcred": "resetcred - EMERGENCY USE ONLY! -- Deletes the 'passwd.txt' file and reboots the terminal to reset all login credentials",
    "lockdown": "lockdown - EMERGENCY USE ONLY! -- Initiates the MANUAL lockout protocol to revoke access to the database until disabled with a LBC",
    "access": "access <SCP-No> - Accesses the SCP <SCP-No>(required), if entered 'random', displays a random SCP",
    "search": "search <keyword> - Search for SCPs containing <keyword>(required) in their title or text",
    "logout": "logout - Logs out from current session to prompt the user with the login interface, added for safety purposes",
    "clean": "clean - Immediately deletes the current Activity Logs folder, and again, yes, added for safety purposes",
    "inco": "inco - Simply, toggles incognito mode, or in another name, toggles logging",
    "evaluate": "evaluate - Works as a complex scientific calculator, allows assigning variables",
    "cls": "cls - Clears the terminal",
    "encrypt": "encrypt <file_path> - Encrypts the specified file, you better save the key or no decryption for you",
    "decrypt": "decrypt <file_path> <key> - Decrypts the specified file with the specified key",
    "trace": "trace <address> - Traces the route to the specified network address",
    "clear": "clear - Clears the terminal",
    "quit": "quit - Exits the terminal",
    "exit": "exit - Exits the terminal",
    "esds": "esds - WARNING! Do not use! Initiates Emergency Self Destruct System!"
}


def show_vars(inc):
    all_vars = {**globals(), **locals()}
    user_vars = {k: v for k, v in all_vars.items() if
                 not k.startswith('__') and not callable(v) and not isinstance(v, types.ModuleType)}
    for var_name, var_value in user_vars.items():
        print(f"{var_name} = {var_value}")
        chronicle_log(f"{var_name} = {var_value}", inc)


def get_command(usr):
    def get_alias(alias):
        conn = LDBConn()
        cursor = conn.cursor()
        cursor.execute('SELECT command FROM alias WHERE alias = ?', (alias,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None

    cmd = input(f"{Fore.CYAN}USER:{usr}::>{Fore.RESET}")
    if cmd and cmd.strip():
        cmd1 = cmd.split()
        mapped_command = get_alias(cmd1[0])
        if mapped_command:
            cmd1[0] = mapped_command
        return cmd1, cmd
    else:
        return None, ''


def encrypt_file(file_path, key):
    with open(file_path, 'rb') as norm_file:
        file_data = norm_file.read()

    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(file_data)

    with open(file_path + ".enc", 'wb') as enc_file:
        enc_file.write(encrypted_data)

    print(f"File {file_path} has been encrypted.")


def decrypt_file(file_path, key):
    with open(file_path, 'rb') as enc_file:
        encrypted_data = enc_file.read()

    fernet = Fernet(key)
    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except Exception as e:
        print(f"Decryption failed: {e}")
        return

    with open(file_path.replace(".enc", ""), 'wb') as norm_file:
        norm_file.write(decrypted_data)

    print(f"File {file_path} has been decrypted.")


def restricted():
    print("")
    print("                                    ", Back.RED + " << ACCESS RESTRICTED >> ")
    print(Fore.RED + "--------------------------------------------------------------------------".center(100))
    print(Fore.RED + "THIS FILE HAS BEEN CLASSIFIED".center(100))
    print(Fore.RED + "<< TOP SECRET >>".center(100))
    print(Fore.RED + "BY ORDER OF THE ADMINISTRATOR".center(100))
    print("")
    print(Fore.RED + "ACCESS TO SCP-001 IS RESCRICTED TO O5 COUNCIL MEMBERS ONLY.".center(100))
    print(Fore.RED + "--------------------------------------------------------------------------".center(100))
    print("")

    print(Fore.YELLOW + "GENERAL NOTICE 001-ALPHA:".center(100))
    print(Fore.YELLOW + "IN ORDER TO PREVENT KNOWLEDGE OF SCP-001 FROM".center(100))
    print(Fore.YELLOW + "BEING LEAKED, SEVERAL/NO FALSE SCP-001 FILES".center(100))
    print(Fore.YELLOW + "HAVE BEEN CREATED ALONGSIDE THE TRUE FILE/FILES.".center(100))
    print(Fore.YELLOW + "ALL FILES CONCERNING THE NATURE OF SCP-001, INCLUDING".center(100))
    print(Fore.YELLOW + "THE DECOY/DECOYS, ARE PROTECTED".center(100))
    print(Fore.YELLOW + "BY A MEMETIC KILL AGENT DESIGNED TO IMMEDIATELY".center(100))
    print(Fore.YELLOW + "CAUSE CARDIAC ARREST IN ANY NONAUTHORIZED PERSONNEL".center(100))
    print(Fore.YELLOW + "ATTEMPTING TO ACCESS THE FILE. REVEALING THE TRUE NATURE/NATURES OF SCP-001".center(100))
    print(Fore.YELLOW + "TO THE GENERAL PUBLIC IS CAUSE FOR EXECUTION.".center(100))
    print(Fore.YELLOW + "EXCEPT AS REQUIRED UNDER ███████-███-████.".center(100))
    print("")

    print(Fore.RED + "--------------------------------------------------------------------------".center(100))
    print(Fore.RED + "ANY NON-AUTHORIZED PERSONNEL ACCESSING THESE DOCUMENTS WILL BE IMMEDIATELY".center(100))
    print(Fore.RED + "TERMINATED THROUGH THE BERRYMAN-LANGFORD MEMETIC KILL AGENT.".center(100))
    print(Fore.RED + "--------------------------------------------------------------------------".center(100))
    print("")


def evaluate_expression(expression):
    try:
        result = eval(expression, globals(), variables)
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def run_calculator(exp, inco):
    expression = exp
    if "=" in expression:
        parts = expression.split("=")
        if len(parts) != 2:
            print("Invalid variable assignment syntax.")
        else:
            var_name = parts[0].strip()
            var_value = parts[1].strip()
            try:
                variables[var_name] = eval(var_value, {}, variables)
                print(f"Variable '{var_name}' assigned.")
                chronicle_log(f"New scientific evaluation var assigned: {var_name}", inco)
            except Exception as e:
                print(f"Error: {str(e)}")
    else:
        result = evaluate_expression(expression)
        print("Result:", result)
        chronicle_log(f"The result of '{expression}' is '{result}'", inco)


for file in os.listdir("CCs"):
    if os.path.isfile(os.path.join("CCs", file)) and file.endswith(".py"):
        module_name = file[:-3]
        module_path = f"CCs.{module_name}"
        module = importlib.import_module(module_path)
        CCS = module.CCS()
        if not CCS.isHidden:
            available_cmds = available_cmds + "\n" + Fore.CYAN + CCS.command + Fore.GREEN + " - " + CCS.help
            if CCS.alias:
                new_alias(CCS.alias, CCS.command)
            else:
                remove_alias(CCS.alias)
            if CCS.detailedHelp:
                cmd_help[CCS.command] = CCS.detailedHelp
        else:
            remove_alias(CCS.alias)
        ccs[CCS.command] = CCS.whenRan


def mainlogonloop(username, password, fromlc, inc, msg=None):
    global incognito
    incognito = inc
    os.system('cls' if os.name == 'nt' else 'clear')
    chronicle_log("<<LOGIN CONFIRMED>>", incognito)
    print(figlet)
    if fromlc:
        print(Fore.BLACK + Back.GREEN + "\t~~~~MANUAL LOCKOUT OVERRIDE CONFIRMED~~~~")
        chronicle_log("<<LOCKOUT OVERRIDDEN>>", incognito)
    print(pyfiglet.figlet_format(f"Welcome Back {username}", font="contessa").center(50))
    if msg:
        print(msg)
    print("Login successful!")
    print(f"Type help to see all available commands")
    if db_deactive:
        print(f"{Back.RED}Failed To Load Database".center(50))
        print(f"{Fore.RED}Access command will be unavailable".center(50))
    while True:
        cmmd, cmd_all = get_command(username)
        if not cmmd:
            continue
        cmd = cmmd[0].lower()
        chronicle_log(f"USER:{username} Ran command: {''.join(cn + ' ' for cn in cmmd)}", incognito)
        if cmd == "quit" or cmd == "exit":
            chronicle_log("<<TERMINAL EXIT>>", incognito)
            quit("Exiting...")
        elif cmd == "logout":
            break
        elif cmd == "clean":
            clean_slate()
            incognito = True
            print(f"{Back.GREEN}Activity logs deleted succesfully{Back.RESET}")
        elif cmd == "usredit":
            usractions(incognito)
        elif cmd == "help":
            if len(cmmd) == 1:
                print(available_cmds)
            elif len(cmmd) >= 3:
                print("This command accepts only one optional argument")
            elif cmmd[1] in cmd_help:
                print(cmd_help[cmd[1]])
            else:
                print("No detailed help available for this command")
        elif cmd == "evaluate":
            if len(cmmd) == 1:
                print(
                    "This command requires an expression to run, you can also type loop as an expression to enter looped calculation mode")
            elif cmd_all.replace("ev ", "evaluate ").lower() == "evaluate loop":
                print(f"{Fore.MAGENTA}Entering Looped Calculation Mode | Type 'EXIT' to quit")
                while True:
                    exp = input("Enter expression: ")
                    if exp == "EXIT":
                        break
                    run_calculator(exp, incognito)
            else:
                run_calculator(cmd_all.replace("ev ", "").replace("evaluate ", ""), incognito)
        elif cmd == "encrypt":
            if len(cmmd) != 2:
                print("Usage: encrypt <file_path>")
            else:
                file_path = cmmd[1]
                if not os.path.isfile(file_path):
                    print(f"File {file_path} does not exist.")
                else:
                    key = Fernet.generate_key()
                    encrypt_file(file_path, key)
                    os.remove(file_path)
                    print(f"Encryption key: {key.decode()} Please store it safely to decrypt the file.")
        elif cmd == "decrypt":
            if len(cmmd) != 3:
                print("Usage: decrypt <file_path> <key>")
            else:
                file_path = cmmd[1]
                key = cmmd[2].encode()
                if not os.path.isfile(file_path):
                    print(f"File {file_path} does not exist.")
                else:
                    decrypt_file(file_path, key)
                    os.remove(file_path)
        elif cmd == "uptime":
            boot_time_timestamp = psutil.boot_time()
            bt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot_time_timestamp))
            current_time = time.time()
            uptime_seconds = current_time - boot_time_timestamp
            uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
            print(f"System boot time: {bt}")
            print(f"Uptime: {uptime_str}")
        elif cmd == "export_scp":
            if len(cmmd) == 1:
                print("Please specify an SCP no and a file format: export_scp <SCP-No> <file_format>")
            elif len(cmmd) >= 4:
                print("This command only accepts two arguments")
            elif len(cmmd) == 2:
                print("Please specify a file format: export_scp <SCP-No> <file_format>")
            elif len(cmmd) == 3:
                export_scp(cmmd[1], cmmd[2])
        elif cmd == "log":
            if len(cmmd) == 1:
                print("Please specify a message with the command: log <msg>")
            elif len(cmmd) >= 3:
                print("This command accepts only one argument")
            elif len(cmmd) == 2:
                if not incognito:
                    chronicle_log(cmmd[1], incognito)
                else:
                    print("Incognito mode active, logging disabled. So not logging your message")
        elif cmd == "trace":
            if len(cmmd) != 2:
                print("Usage: trace <address>")
            else:
                address = cmmd[1]
                try:
                    subprocess.run(["tracert", address])
                except Exception as e:
                    print(f"Error executing tracert: {e}")
        elif cmd == "notice":
            if len(cmmd) == 1:
                print("""Availaable Sub-Commands:
                add <SCP No.> <type> <extra> <notice> <Unique Identifier>
                remove <SCP No.> <Unique Identifier>""")
            elif cmmd[1] == "add":
                if len(cmmd) != 6:
                    print(f"""Usage:
                    notice add <SCP No.> <type> <extra> <Unique Identifier>
                    eg. notice add SCP-173 {Fore.GREEN}General{Fore.CYAN} 001-ALPHA{Fore.RESET} N01
                    Enter notice | 'END' to end: {Fore.MAGENTA}This is a notice{Fore.RESET}
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                    This will bring out the text below when SCP-173 is accessed:
                    {Fore.GREEN}General{Fore.RESET} Notice {Fore.CYAN}001-ALPHA{Fore.RESET}: {Fore.MAGENTA}This is a notice""")
                else:
                    current = 1
                    looping = True
                    no = cmmd[2]
                    not_type = cmmd[3]
                    extra = cmmd[4]
                    identifier = cmmd[5]
                    notice = ""
                    while looping:
                        if current == 1:
                            line = input("Enter first line: ")
                            current = 0
                        else:
                            line = "\n" + input("Enter new line | 'END' to end: ")
                        if line.strip() != "END":
                            notice += line
                        else:
                            looping = False
                    add_notice(no, not_type, extra, notice, identifier)
            elif cmmd[1] == "remove":
                if len(cmmd) != 4:
                    print("""Usage:
                    notice remove <SCP No.> <Unique Identifier>""")
                else:
                    no = cmmd[2]
                    identifier = cmmd[3]
                    rem_notice(no, identifier)
        elif cmd == "alias":
            if len(cmmd) == 1:
                print("""Available Sub-commands:
                list
                add [alias] [command]
                remove [alias]""")
            elif cmmd[1] == "list":
                conn = LDBConn()
                cursor = conn.cursor()
                cursor.execute('SELECT alias, command FROM alias')
                rows = cursor.fetchall()
                for row in rows:
                    print(f"{row[0]} = {row[1]}")
                conn.close()
            elif cmmd[1] == "add":
                if len(cmmd) != 4:
                    print("Usage: alias add [alias] [command]")
                else:
                    alias = cmmd[2]
                    command = cmmd[3]
                    conn = LDBConn()
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1 FROM alias WHERE alias = ?', (alias,))
                    if cursor.fetchone() is None:
                        cursor.execute('INSERT INTO alias (alias, command) VALUES (?, ?)', (alias, command))
                        print(f"Alias '{alias}' added with command '{command}'.")
                    else:
                        print(f"Alias '{alias}' already exists.")
                    conn.commit()
                    conn.close()
            elif cmmd[1] == "remove":
                if len(cmmd) != 3:
                    print("Usage: alias remove [alias]")
                else:
                    alias = cmmd[2]
                    conn = LDBConn()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM alias WHERE alias = ?', (alias,))
                    if cursor.rowcount > 0:
                        print(f"Alias '{alias}' removed.")
                    else:
                        print(f"Alias '{alias}' not found.")
                    conn.commit()
                    conn.close()
        elif cmd == "search":
            if len(cmmd) > 1:
                search(cmmd, incognito)
            else:
                print("Search command requires a keyword")
        elif cmd == "inco":
            incognito = not incognito
            print(f"{Fore.YELLOW}Current INCOGNITO state: {incognito}")
        elif cmd == "update":
            update_dataset(incognito)
        elif cmd == "vars":
            show_vars(incognito)
        elif cmd == "lockdown":
            rusure = input("""This will initiate an immediate lockout procedure on your current frontend!
    And it will not be able to disabled without the LBC!
    Are you sure? This will require your password to be entered. Y/N: """)
            if rusure.lower() == "y":
                paswd = input("Please enter your password(Enter EXIT to exit): ")
                if paswd == password:
                    set_lockout(1, 1)
                    print("Lockout initiated")
                    chronicle_log("<<TERMINAL MANUAL LOCKOUT INITIATED>>", incognito)
                    break
                elif paswd == "EXIT":
                    print("Command terminated")
                    break
                else:
                    print("Wrong password!")
            else:
                print("Command terminated")
        elif cmd == "access":
            if len(cmmd) == 1:
                print("Please use the command with an SCP No or enter 'random' to access a random SCP")
            elif len(cmmd) >= 3:
                print("This command only accepts one argument")
            elif len(cmmd) == 2:
                if cmmd[1].lower() == "random":
                    rand = random.randint(1, 6999)
                    frand = f"{rand:04d}" if rand >= 1000 else f"{rand:03d}"
                    chronicle_log(f"Random SCP -> SCP-{frand} accessed", incognito)
                    access(frand)
                elif cmmd[1] == "001" or cmmd[1].lower() == "scp-001":
                    access_anim(f"{Fore.RED}ACCESS DENIED{Fore.RESET}", 10)
                    chronicle_log("<<ACCESS TO SCP-001 IS RESTRICTED TO O5 COUNCIL MEMBERS>>", incognito)
                    restricted()
                else:
                    try:
                        cmmmd = int(cmmd)
                        acc = f"{cmmmd:04d}" if cmmmd >= 1000 else f"{cmmmd:03d}"
                        chronicle_log(f"SCP-{acc} accessed", incognito)
                        access(acc)
                    except TypeError:
                        chronicle_log(f"{cmmd[1]} accessed", incognito)
                        access(cmmd[1])
        elif cmd == "cls" or cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            chronicle_log("<<TERMINAL CLEARED>>", incognito)
        elif cmd in ccs:
            ccs[cmd](cmmd, cmd_all)
        elif cmd == "esds":
            os.system('cls' if os.name == 'nt' else 'clear')
            run_esds(incognito)
        else:
            print(f"{Fore.RED}{cmd} is not an internal or external command | Error: Command Not Found")
            chronicle_log(f"{cmd} is an unknown command", incognito)


if __name__ == '__main__':
    print("This file includes necessary command handling functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
