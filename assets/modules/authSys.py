import os
from time import sleep as sl
import bcrypt
from cryptography.fernet import Fernet
import colorama
from colorama import Fore, Back, Style
import getpass
import uuid
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import base64
import hashlib
import pyotp
from modules.dbUtils import LDBConn, GDBConn

colorama.init(autoreset=True)


# Define command aliases
aliases = {
    'h': 'help',
    'r': 'resetcred',
    'v': 'vars',
    'ld': 'lockdown',
    'u': 'update',
    'ac': 'access',
    'ue': 'usrEdit',
    'al': 'alias',
    's': 'search',
    'ev': 'evaluate',
    'l': 'logout',
    'cl': 'clean',
    'i': 'inco',
    'c': 'cls',
    'q': 'quit',
    'e': 'exit',
    'ch': 'chat',
    'enc': 'encrypt',
    'dec': 'decrypt',
    'tr': 'trace'
}


def get_device_fingerprint():
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()


def generate_fernet_key(input_key):
    # Ensure the key is 32 bytes
    key = hashlib.sha256(input_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


# Function to mask input for sensitive information
def mask_input(prompt=''):
    return getpass.getpass(prompt)


#TODO: Work on this function later

# Function to initialize the database
def initialize_db():
    # Init Global Database
    # FIXME: This part needs to be removed from here, find a solution
    gconn = GDBConn()
    gcursor = gconn.cursor()
    gcursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        o5_code_hash TEXT NOT NULL,
        email TEXT NOT NULL,
        tfa TEXT NOT NULL,
        totp_secret TEXT NOT NULL
    )''')
    gcursor.execute('''CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txx TEXT NOT NULL,
        value INTEGER NOT NULL
    )''')
    gcursor.execute('''CREATE TABLE IF NOT EXISTS keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        key_hash TEXT NOT NULL
    )''')
    gcursor.execute('''CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        no TEXT NOT NULL,
        notice TEXT NOT NULL,
        identifier TEXT UNIQUE NOT NULL
    )''')
    gcursor.execute('''CREATE TABLE IF NOT EXISTS fingerprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        fingerprint TEXT NOT NULL
    )''')
    gcursor.execute('SELECT 1 FROM actions WHERE txx = ?', ('lockout',))
    if gcursor.fetchone() is None:
        gcursor.execute('INSERT INTO actions (txx, value) VALUES (?, ?)', ('lockout', 0))
    gconn.commit()
    gconn.close()
    # Init Local Database
    lconn = LDBConn()
    lcursor = lconn.cursor()
    lcursor.execute('''CREATE TABLE IF NOT EXISTS alias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT NOT NULL,
    command TEXT NOT NULL
    )''')
    lcursor.execute('''CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txx TEXT NOT NULL,
        value INTEGER NOT NULL
    )''')
    lcursor.execute('SELECT 1 FROM actions WHERE txx = ?', ('lockout',))
    if lcursor.fetchone() is None:
        lcursor.execute('INSERT INTO actions (txx, value) VALUES (?, ?)', ('lockout', 0))
    lcursor.execute('SELECT 1 FROM actions WHERE txx = ?', ('cbd',))
    if lcursor.fetchone() is None:
        lcursor.execute('INSERT INTO actions (txx, value) VALUES (?, ?)', ('cbd', 0))
    lconn.commit()
    lconn.close()


# Function to initialize command aliases
def initialize_aliases():
    conn = LDBConn()
    cursor = conn.cursor()
    for alias, command in aliases.items():
        cursor.execute('SELECT 1 FROM alias WHERE alias = ?', (alias,))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO alias (alias, command) VALUES (?, ?)', (alias, command))
    conn.commit()
    conn.close()


def new_alias(alias, cmd):
    conn = LDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM alias WHERE alias = ?', (alias,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO alias (alias, command) VALUES (?, ?)', (alias, cmd))
    conn.commit()
    conn.close()


def remove_alias(alias):
    conn = LDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM alias WHERE alias = ?', (alias,))
    if cursor.fetchone() is not None:
        cursor.execute('DELETE FROM alias WHERE alias = ?', (alias,))
    conn.commit()
    conn.close()


def add_notice(no, not_type, extra, notice, identifier):
    if no.lower().startswith("scp-"):
        no = no.upper()
    else:
        no = "SCP-" + str(no)
    final = not_type + " Notice " + extra + ": " + notice
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM notices WHERE no = ? AND identifier = ?", (no, identifier,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO notices (no, notice, identifier) VALUES (?, ?, ?)', (no, final, identifier,))
        conn.commit()
        conn.close()
    else:
        print(f"{Fore.RED}The Notice With The Same SCP No and identifier already exists!")


def rem_notice(no, identifier):
    if no.lower().startswith("scp-"):
        no = no.upper()
    else:
        no = "SCP-" + str(no)
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM notices WHERE no = ? AND identifier = ?', (no, identifier,))
    if cursor.fetchone() is not None:
        cursor.execute('DELETE FROM notices WHERE no = ? AND identifier = ?', (no, identifier,))
        conn.commit()
        conn.close()
    else:
        print(f"{Fore.RED}The Notice You Are Looking For Doesn't Exist")


# Helper function to send 2FA code via email
def send_2fa_code(email):
    code = random.randint(100000, 999999)
    sender_email = "mbaai.com.tr"
    sender_password = "1235789"

    msg = MIMEMultipart()
    msg['From'] = "protonme@" + sender_email
    msg['To'] = email
    msg['Subject'] = "Your 2FA Code"

    body = f"Your 2FA code is {code}"
    msg.attach(MIMEText(body))

    try:
        server = smtplib.SMTP('smtp.smtp2go.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail("protonme@" + sender_email, email, msg.as_string())
        server.quit()
        return code
    except Exception as e:
        print(Fore.RED + f"ERROR: Failed to send 2FA code. {e}")
        return None


def check_for_notices(no):
    if no.lower().startswith("scp-"):
        no = no.upper()
    else:
        no = "SCP-" + str(no)
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT notice FROM notices WHERE no = ?', (no,))
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result


# Function to check if it's the first launch of the program
def is_first_launch():
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0


# Function to check if a username already exists
def username_exists(username):
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


# Function to get new user credentials
def get_new_creds():
    while True:
        username = input("Enter new username: ")
        if username_exists(username):
            print(f"{Fore.RED}Username already exists, try again!")
            continue
        break
    while True:
        password = mask_input("Enter new password: ")
        conf_password = mask_input("Confirm password: ")
        if password == conf_password:
            final_pass = password
            break
        else:
            print(f"{Fore.RED}Passwords aren't the same, try again!")
    while True:
        o5 = mask_input("Enter new LockoutBackupCode: ")
        o5_conf = mask_input("Confirm LockoutBackupCode: ")
        if o5 == o5_conf:
            final_o5 = o5
            break
        else:
            print(f"{Fore.RED}Codes aren't the same, try again!")
    while True:
        email = input("Enter new email: ")
        email_conf = input("Confirm email: ")
        if email == email_conf:
            final_email = email
            break
        else:
            print(Fore.RED + "Emails aren't the same, try again!")
    tfa = not input("Do you want to enable 2FA | Y/n: ").lower() == "n"
    return username, final_pass, final_o5, final_email, tfa


# Function to get user credentials
def get_credentials():
    while True:
        username = input("Enter username: ")
        password = mask_input("Enter password: ")
        return username, password


# Function to get O5 credentials
def get_o5_credentials():
    while True:
        usr = input(Fore.RED + "Enter Username: " + Fore.RESET)
        pas = mask_input(Fore.RED + "Enter Password: " + Fore.RESET)
        o5 = mask_input(Fore.RED + "Enter LBC: " + Fore.RESET)
        return usr, pas, o5


# Function to save user credentials
def save_credentials(username, password, o5, email, tfa):
    conn = GDBConn()
    cursor = conn.cursor()
    secret = pyotp.random_base32()
    print("Getting device fingerprint...")
    fingerprint = get_device_fingerprint()
    crypt_suite = Fernet(generate_fernet_key(username))
    secret_enc = crypt_suite.encrypt(secret.encode())
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    hashed_o5 = bcrypt.hashpw(o5.encode(), salt)
    cursor.execute('INSERT INTO users (username, password_hash, o5_code_hash, email, tfa, totp_secret) VALUES (?, ?, ?, ?, ?, ?)',
                   (username, hashed_password.decode(), hashed_o5.decode(), email, tfa, secret_enc,))
    cursor.execute('INSERT INTO fingerprints (user, fingerprint) VALUES (?, ?)', (username, fingerprint,))
    conn.commit()
    conn.close()
    print(f"TOTP secret for username {username}: {secret}")
    print("Please add this to your authenticator application")
    input("Press enter when you wish to continue...")
    input("Please actually save the key in case you haven't saved it, press enter to continue...")


# Function to check user credentials
def check_credentials(username, password):
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    cursor.execute('SELECT fingerprint FROM fingerprints WHERE user = ?', (username,))
    result1 = cursor.fetchone()
    result1 = [] if result1 is None else result1
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        cursor.execute('SELECT tfa FROM users WHERE username = ?', (username,))
        fetch = cursor.fetchone()
        fetch = False if fetch is None else int(fetch[0])
        if fetch:
            cursor.execute('SELECT email FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            code = send_2fa_code(result[0])
            c = input("Enter the 2FA code sent to your email: ")
            if c == str(code):
                if not os.path.exists(".nofpa"):
                    if not get_device_fingerprint() in result1:
                        if not input(
                                "This devices fingerprint wasn't added to the database. Do you want to add it now? -> Y/n: ").lower() == "n":
                            print("Adding fingerprint to database...")
                            cursor.execute('INSERT INTO fingerprints (user, fingerprint) VALUES (?, ?)',
                                           (username, get_device_fingerprint()))
                        else:
                            if input("Do you want to disable this notification? -> y/N: ").lower() == "y":
                                with open(".nofpa", 'wb'):
                                    pass
                conn.close()
                return True
            else:
                conn.close()
                return False
        else:
            if not os.path.exists(".nofpa"):
                if not get_device_fingerprint() in result1:
                    if not input("This devices fingerprint wasn't added to the database. Do you want to add it now? -> Y/n: ").lower() == "n":
                        print("Adding fingerprint to database...")
                        cursor.execute('INSERT INTO fingerprints (user, fingerprint) VALUES (?, ?)', (username, get_device_fingerprint()))
                    else:
                        if input("Do you want to disable this notification? -> y/N: ").lower() == "y":
                            with open(".nofpa", 'wb'):
                                pass
            conn.close()
            return True
    else:
        conn.close()
        return False


# Function to check O5 credentials
def check_o5_credentials(user, pasw, o5pass):
    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash, o5_code_hash FROM users WHERE username = ?', (user,))
    result = cursor.fetchone()
    if result and bcrypt.checkpw(pasw.encode(), result[0].encode()) and bcrypt.checkpw(o5pass.encode(),
                                                                                       result[1].encode()):
        cursor.execute('SELECT tfa FROM users WHERE username = ?', (user,))
        tfa = cursor.fetchone()
        tfa = False if tfa is None else int(tfa[0])
        if int(tfa):
            cursor.execute('SELECT email FROM users WHERE username = ?', (user,))
            result = cursor.fetchone()
            code = send_2fa_code(result[0])
            c = input("Enter 2FA code sent to your email: ")
            if c == str(code):
                conn.close()
                return True
            else:
                conn.close()
                return False
        else:
            conn.close()
            return True
    else:
        return False


# Function to set lockout values
def set_lockout(value, cbd):
    conn = LDBConn()
    cursor = conn.cursor()
    cursor.execute('UPDATE actions SET value = ? WHERE txx = ?', (value, 'lockout'))
    cursor.execute('UPDATE actions SET value = ? WHERE txx = ?', (cbd, 'cbd'))
    conn.commit()
    conn.close()


# Function to get lockout values
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
        cursor.execute('SELECT value FROM actions WHERE idn = ?', ('lockout',))
        result = cursor.fetchone()
        cursor.execute('SELECT value FROM actions WHERE idn = ?', ('cbd',))
        result1 = cursor.fetchone()
        conn.close()
        if result:
            final[0] = result[0]
        else:
            final[0] = 0
        if result1:
            final[1] = result1[0]
        else:
            final[1] = 0
        return final


if __name__ == '__main__':
    print("This file includes necessary authentication functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
