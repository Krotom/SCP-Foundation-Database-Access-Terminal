try:
    import os
    from time import sleep as sl
    import pyfiglet
    import colorama
    from modules.dbUtils import LDBConn
    from colorama import Fore
    from lockoutProtocol import lock_protocol
    import sqlite3

    # Prompt user to skip PIP install sequence
    if input("SKIP PIP INSTALL SEQUENCE (Not Recommended For First Run) y/N: ").lower() == "y":
        print("PIP SEQUENCE SKIPPED - NORMAL OPERATION CONTINUE")
        sl(0.2)
    else:
        os.system(
            "%cd%\\Python\\python.exe -m pip install --upgrade pip bcrypt pandas pyfiglet colorama psutil requests cryptography sqlitecloud pyotp pyreadline3 --no-warn-script-location"
        )

    # Try importing modules
    if os.path.exists("modules"):
        from modules.chronicle_engine import chronicle_log
        from modules.authSys import is_first_launch, get_new_creds, get_credentials, save_credentials, check_credentials, initialize_db, set_lockout, initialize_aliases
        initialize_db()
        initialize_aliases()
        from modules.commandHandler import mainlogonloop

    colorama.init(autoreset=True)

    # Progress bar function
    def progress(percent=0, width=30):
        symbol = width * percent // 100
        blanks = width - symbol
        print('\r[ ', Fore.GREEN + symbol * "█", blanks * ' ', ' ]', f' {percent:.0f}%', sep='', end='', flush=True)


    # Display progress bar
    for i in range(101):
        progress(i)
        sl(0.01)
    print()

    figlet = pyfiglet.figlet_format("SCP", font="doh") + Fore.LIGHTCYAN_EX + pyfiglet.figlet_format("Foundation", font="standard")
    figlet = str(figlet).replace("\n", "\n\t\t\t")

    # REM: Don't forget to uncomment the begin log line after development

    # Begin log - Disabled for debugging
    # chronicle_log("<<BEGIN LOG>>", False)

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
            final = [0, 0]
            conn = LDBConn()
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM actions WHERE txx = ?', ('lockout',))
            result = cursor.fetchone()
            cursor.execute('SELECT value FROM actions WHERE txx = ?', ('cbd',))
            result1 = cursor.fetchone()
            conn.close()
            if result:
                final[0] = result[0]
            if result1:
                final[1] = result1[0]
            return final

    # Main function
    def main():
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(figlet)
            print(pyfiglet.figlet_format("Welcome Back", font="digital"))
            if not get_lockout(False):
                if is_first_launch():
                    print(f"{Fore.LIGHTCYAN_EX}First launch detected!")
                    print("Please create the first user!")
                    username, password, o5, email, tfa = get_new_creds()
                    save_credentials(username, password, o5, email, tfa)
                    print(f"{Fore.GREEN}Credentials saved successfully.")
                    chronicle_log("<<MAIN USER CREATED>>", False)
                    mainlogonloop(username, password, False, False)
                else:
                    attempts = 3
                    while attempts > 0:
                        username, password = get_credentials()
                        if "-preinco" not in username:
                            if check_credentials(username, password):
                                mainlogonloop(username, password, False, False)
                                break
                            else:
                                attempts -= 1
                                print(f"{Fore.RED}Invalid credentials. Please try again. Attempts left:", attempts)
                                chronicle_log("<<INVALID CREDS ENTERED>>", False)
                        else:
                            if check_credentials(username.replace("-preinco", ""), password):
                                mainlogonloop(username.replace("-preinco", ""), password, False, True, msg=f"{Fore.MAGENTA}Launching in INCOGNITO mode")
                                break
                            else:
                                attempts -= 1
                                print(f"{Fore.RED}Invalid credentials. Please try again. Attempts left:", attempts)
                                chronicle_log("<<INVALID CREDS ENTERED>>", False)
                    else:
                        set_lockout(1, 1)
                        print(f"{Fore.RED}Lockout initiated")
                        chronicle_log("<<TERMINAL AUTOMATIC LOCKOUT INITIATED>>", False)
            else:
                lock_protocol()
  
  
    main()
except Exception as e:
    print(f"Terminal shutting down due to an unhandled error: {e}")
