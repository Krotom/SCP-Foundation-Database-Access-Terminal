import sqlite3
import bcrypt
import pyfiglet
import colorama
from modules.dbUtils import GDBConn
from colorama import Fore
from modules.authSys import mask_input, save_credentials, check_credentials, get_credentials, get_new_creds
from modules.chronicle_engine import chronicle_log

colorama.init(autoreset=True)
figlet = pyfiglet.figlet_format("SCP", font="doh") + Fore.LIGHTCYAN_EX + pyfiglet.figlet_format("Foundation", font="standard")
figlet = str(figlet).replace("\n", "\n\t\t\t")


def remove_user(username, password, incognito):
    if check_credentials(username, password):
        conn = GDBConn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        print(f"User {username} removed successfully.")
        chronicle_log(f"<<USER {username} REMOVED FROM DB>>", incognito)
    else:
        print("Invalid credentials. User not removed.")
        chronicle_log(f"<<INVALID CREDS, USER {username} NOT REMOVED>>", incognito)


def change_password(username, old_password, new_password, incognito):
    if check_credentials(username, old_password):
        conn = GDBConn()
        cursor = conn.cursor()
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode(), salt)
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (hashed_password.decode(), username))
        conn.commit()
        conn.close()
        print(f"Password for user {username} updated successfully.")
        chronicle_log(f"<<PASSWORD FOR USER {username} UPDATED>>", incognito)
    else:
        print("Invalid credentials. Password not changed.")
        chronicle_log(f"<<INVALID CREDS, PASSWORD FOR USER {username} NOT CHANGED>>", incognito)


def add_user(incognito):
    username, password, o5, email = get_new_creds()
    save_credentials(username, password, o5, email)
    print(f"User {username} added successfully.")
    chronicle_log(f"<<USER {username} ADDED TO DB>>", incognito)


def main(incognito):
    while True:
        print(figlet)
        print("\nUser Management System")
        print("1. Add User")
        print("2. Remove User")
        print("3. Change User Password")
        print("4. Exit")
        choice = input("<:--USRManagement--:> Selection: ")

        if choice == '1':
            add_user(incognito)
        elif choice == '2':
            username, password = get_credentials()
            remove_user(username, password, incognito)
        elif choice == '3':
            username, old_password = get_credentials()
            new_password = mask_input("Enter new password: ")
            change_password(username, old_password, new_password, incognito)
        elif choice == '4':
            break
        else:
            print("INVALID")


if __name__ == '__main__':
    print("This file includes necessary user functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
