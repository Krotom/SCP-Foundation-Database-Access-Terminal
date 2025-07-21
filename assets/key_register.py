from modules.authSys import mask_input
from modules.dbUtils import GDBConn
import sqlite3
import bcrypt
import colorama
from cryptography.fernet import Fernet
import os
from colorama import Fore, Back
from os import system as s
import base64
import hashlib


def generate_fernet_key(input_key):
    # Ensure the key is 32 bytes
    key = hashlib.sha256(input_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


s("cls")
colorama.init(autoreset=True)
if not mask_input("Please enter Gen-Alpha style password: ") == "skibidirizzlergyattmustafa":
    print("INVALID")
    exit("INVALID")
s("cls")
print(Fore.RED + "<<ESDS ACTIVASION KEY REGISTRATION SYSTEM>>".center(150))
print("WELCOME BACK".center(150))
print("\n\n")

uname = input("                                                  Please enter the username to register the key to: ")
while True:
    passwd = mask_input("                                                                Please enter the key: ")
    if len(passwd) <= 14:
        print("Sorry, The password can't be shorter than 15 chars for security reasons".center(150))
    else:
        break
while True:
    key_conf1_input = mask_input("                                                           Please enter encryption key 1: ")
    if len(key_conf1_input) <= 7:
        print("Sorry, Encryption keys cant be shorter than 8 chars for security reasons".center(150))
    else:
        break
while True:
    key_conf2_input = mask_input("                                                           Please enter encryption key 2: ")
    if len(key_conf2_input) <= 7:
        print("Sorry, Encryption keys cant be shorter than 8 chars for security reasons".center(150))
    else:
        break
while True:
    key_conf3_input = mask_input("                                                         Please enter encryption key ALPHA: ")
    if len(key_conf3_input) <= 7:
        print("Sorry, Encryption keys cant be shorter than 8 chars for security reasons".center(150))
    else:
        break

# Generate valid Fernet keys
key_conf1 = generate_fernet_key(key_conf1_input)
key_conf2 = generate_fernet_key(key_conf2_input)
key_conf3 = generate_fernet_key(key_conf3_input)

try:
    conn = GDBConn()
    cursor = conn.cursor()
    fernet = Fernet(key_conf1)
    fernet2 = Fernet(key_conf2)
    fernetAlpha = Fernet(key_conf3)
    key_hash = fernet.encrypt(passwd.encode())
    key_hash = fernet2.encrypt(key_hash)
    cursor.execute('SELECT 1 FROM keys WHERE user = ?', (uname,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO keys (user, key_hash) VALUES (?, ?)', (uname, key_hash))
        print(Fore.CYAN + "Key Added To Database".center(150))
    else:
        print(Fore.RED + "A key is already registered to this username(Yeah, I know I should have said it earlier!)")
    conn.commit()
    conn.close()
    key_conf1 = fernetAlpha.encrypt(key_conf1).decode()
    key_conf2 = fernetAlpha.encrypt(key_conf2).decode()
    print(f"Decryption key 1: {key_conf1}".center(150))
    print(f"Decryption key 2: {key_conf2}".center(150))
    print("Decryption key ALPHA: --**{DATA EXPUNGED}**-- (This is the same as the Encryption Key ALPHA!)".center(150))
    print(Back.RED + "Please save these for later use!".center(150))
    with open("keys.txt", 'w') as f:
        f.write(f"Decryption key 1: {key_conf1}\n")
        f.write(f"Decryption key 2: {key_conf2}\n")
        f.write("Decryption key ALPHA: --**{DATA EXPUNGED}**-- (This is the same as the Encryption Key ALPHA! So you already know this!)")
    print("Your keys will also be saved in the keys.txt file within the assets folder! You can move it to somewhere else!")
    input("Paused for you to save your keys! Press enter to terminate the program...")
except Exception as e:
    print(Fore.RED + f"ERROR: {e}".center(150))
