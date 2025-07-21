import os
from time import sleep as sl
import colorama
from colorama import Fore, Back, Style
import pyfiglet

colorama.init(autoreset=True)

figlet = pyfiglet.figlet_format("SCP", font="doh") + Fore.LIGHTCYAN_EX + pyfiglet.figlet_format("Foundation", font="standard")
figlet = str(figlet).replace("\n", "\n\t\t\t")

# Try importing modules
try:
    from modules.authSys import get_o5_credentials, check_o5_credentials, set_lockout
    from modules.dbUtils import LDBConn
    from modules.commandHandler import mainlogonloop
except Exception:
    pass


# Function to get lockout status
def get_lockout(cbd):
    if not cbd:
        conn = LDBConn()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM actions WHERE txx = ?', ('lockout',))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return 0
    else:
        final = [None, None]
        conn = LDBConn()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM actions WHERE txx = ?', ('lockout',))
        result = cursor.fetchone()
        cursor.execute('SELECT value FROM actions WHERE txx = ?', ('cbd',))
        result1 = cursor.fetchone()
        conn.close()
        final[0] = result[0] if result else 0
        final[1] = result1[0] if result1 else 0
        return final


# Function to display a progress bar
def progress(percent=0, width=30):
    symbol = width * percent // 100
    blanks = width - symbol
    print('\r[ ', Fore.GREEN + symbol * "█", blanks * ' ', ' ]',
          f' {percent:.0f}%', sep='', end='', flush=True)


# Function to handle lockout protocol
def lock_protocol():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(figlet)
    print(Fore.RED + '''
                ▀▀█▀▀ █▀▀▀  █▀▀█  █▀▄▀█ ▀█▀  █▄  █  █▀▀█  █       █     █▀▀▀█  █▀▀█  █ ▄▀  █▀▀▀  █▀▀▄  
                  █   █▀▀▀  █▄▄▀  █ █ █  █   █ █ █  █▄▄█  █       █     █   █  █     █▀▄   █▀▀▀  █  █  
                  █   █▄▄▄  █  █  █   █ ▄█▄  █  ▀█  █  █  █▄▄█    █▄▄█  █▄▄▄█  █▄▄█  █  █  █▄▄▄  █▄▄▀  ''')
    print("")
    if get_lockout(True)[1]:
        print("                                ", Back.RED + " << EMERGENCY LOCKOUT PROTOCOL INITIATED >> ")
    else:
        print("                            ", Back.RED + " << EMERGENCY SELF DESTRUCT SYSTEM INITIATED >> ")
    print("")

    while True:
        if get_lockout(True)[1]:
            usr, pas, o5 = get_o5_credentials()
            if check_o5_credentials(usr, pas, o5):
                set_lockout(0, 0)
                print("")
                print(Fore.YELLOW + "\tLOCKOUT PROTOCOL OVERRIDDEN")
                for fi in range(101):
                    progress(fi)
                    sl(0.001)
                mainlogonloop(usr, pas, True, True)
                break
            else:
                print("")
                print("      ", Fore.BLACK + Back.RED + " INVALID LOCKOUT BACKUP CODE ")
                print(Fore.RED + "       << TERMINAL LOCKED >>")
                sl(7300)


if __name__ == '__main__':
    print("This file includes necessary lockout functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
