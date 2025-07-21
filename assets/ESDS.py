import time
import sqlite3
import bcrypt
import random
import shutil
import os
import uuid
from modules.dbUtils import LDBConn, GDBConn
from cryptography.fernet import Fernet
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import colorama
from colorama import Fore, Back
import base64
import hashlib
import pyotp
colorama.init(autoreset=True)


def generate_fernet_key(input_key):
    # Ensure the key is 32 bytes
    key = hashlib.sha256(input_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


if os.path.exists("modules"):
    from modules.chronicle_engine import chronicle_log
    from modules.authSys import mask_input, set_lockout
    from modules.animations import anim


# Helper function to send 2FA code via email
def send_2fa_code(email, incog):
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
        chronicle_log(f"Failed to send 2FA code to {email}: {e}", incog)
        return None


def get_device_fingerprint():
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()


# noinspection PyArgumentList
def device_fingerprint_verification(user, incog):
    print("CHECKING DEVICE FINGERPRINT...")
    device_fingerprint = get_device_fingerprint()

    conn = GDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT fingerprint FROM fingerprints WHERE user = ?', (user,))
    stored_fingerprint_hash = cursor.fetchone()
    conn.close()

    if device_fingerprint in stored_fingerprint_hash:
        chronicle_log("Device fingerprint verification passed.", incog)
        return True
    else:
        chronicle_log("Device fingerprint verification failed.", incog)
        return False


# Function to check ESDS credentials
def check_esds_creds(incog):
    try:
        print("AUTHENTICATION STEP 2 - LOGIN CREDENTIALS AND DEVICE FINGERPRINT CHECK")
        user = input("Enter username: ")
        dfv = device_fingerprint_verification(user, incog)
        if not dfv:
            print("DEVICE FINGERPRINT VERIFICATION FAILED")
            return False
        else:
            print("SUCCESS!")
        pasw = mask_input("Enter password: ")
        o5pass = mask_input("Enter LBC: ")
        print("AUTHENTICATION STEP 3 - ESDS ACTIVATION KEY")
        key_usr = input("Enter the username where your ESDS key is stored in: ")
        key = mask_input("Enter your ESDS key: ")
        print(f"{Fore.RED}PLEASE LOOK CAREFULLY TO THE NAMES OF THE PASSWORDS FROM NOW ON, SINCE THEY CAN BE MISUNDERSTOOD EASILY")
        key_enc1 = mask_input("Enter ENcryption key 1: ")
        key_enc2 = mask_input("Enter ENcryption key 2: ")
        key_conf1 = input("Enter DEcryptionDecryption key 1: ")
        key_conf2 = input("Enter DEcryptionDecryption key 2: ")
        key_conf3 = mask_input("Enter DEcryptionDecryption key ALPHA: ")

        key_enc1 = generate_fernet_key(key_enc1)
        key_enc2 = generate_fernet_key(key_enc2)
      
        fernetalpha = Fernet(generate_fernet_key(key_conf3))
        key_conf1 = fernetalpha.decrypt(key_conf1.encode()).decode()
        key_conf2 = fernetalpha.decrypt(key_conf2.encode()).decode()

        fernet1 = Fernet(key_conf1)
        fernet2 = Fernet(key_conf2)

        # Connect to the database and fetch user credentials
        conn = LDBConn()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, o5_code_hash, email FROM users WHERE username = ?', (user,))
        result = cursor.fetchone()
        cursor.execute('SELECT key_hash FROM keys WHERE user = ?', (key_usr,))
        result1 = cursor.fetchone()
        conn.close()

        key_hash = result1[0]
        key_hash = fernet2.decrypt(key_hash)
        key_hash = fernet1.decrypt(key_hash)
        # Validate credentials
        if result and result1 and bcrypt.checkpw(pasw.encode(), result[0].encode()) and bcrypt.checkpw(o5pass.encode(), result[1].encode()) and key_conf1 == key_enc1 and key_conf2 == key_enc2 and key_hash == bytes(key.encode()):
            print("AUTHENTICATION STEP 4 - 2FA CODE")
            email = result[2]
            code = send_2fa_code(email, incog)
            if code is None:
                return False
            user_code = input("Enter the 2FA code sent to your email: ")
            if user_code == str(code):
                print("AUTHENTICATION STEP 5 - TOTP CODE")
                inp = input(f"Enter TOTP code for user {user}: ")
                if verify_totp(user, inp):
                    chronicle_log(f"User {user} successfully authenticated for ESDS operation.", incog)
                    return True
            else:
                print(Fore.RED + "Invalid 2FA code.")
                chronicle_log(f"User {user} failed 2FA authentication.", incog)
                return False
        else:
            print(Fore.RED + "Incorrect credentials.")
            chronicle_log(f"Failed ESDS credential check for user {user}.", incog)
            return False

    except Exception as e:
        print(Fore.RED + f"ERROR: {e}")
        chronicle_log(f"Error during ESDS credential check: {e}", incog)
        return False


# Function to ask a math question as a security measure
def math_question(incog):
    try:
        while True:
            equations = ['*', '/', '+', '-']
            num1 = random.randint(1, 50)
            num2 = random.randint(1, 50)
            eq = random.choice(equations)
            real = eval(f"{num1} {eq} {num2}")
            if type(real) is float or real > 75 or real <= 0:
                continue
            print(f"AUTHENTICATION STEP 1 - SECURITY QUESTION -> {num1} {eq} {num2} = ?")
            answer = input("ANSWER -> ? =  ")
            if answer == str(real):
                chronicle_log("Security question answered correctly.", incog)
                return True
            else:
                chronicle_log("Security question answered incorrectly.", incog)
                return False
    except Exception as e:
        print(Fore.RED + f"ERROR: {e}")
        chronicle_log(f"Error during security question: {e}", incog)
        return False


# Function to corrupt a file
def corrupt_file(file_path, corruption_percentage=100):
    try:
        with open(file_path, 'rb') as file:
            data = bytearray(file.read())

        num_corrupt_bytes = int(corruption_percentage / 100 * len(data))

        for _ in range(num_corrupt_bytes):
            print(f"\r{_}/{num_corrupt_bytes} corrupted...", end="", flush=True)
            index = random.randint(0, len(data) - 1)
            data[index] = random.randint(0, 255)

        with open(file_path, 'wb') as file:
            file.write(data)
    except Exception as e:
        print(Fore.RED + f"ERROR: Could not corrupt file {file_path}. {e}")


# Function to verify TOTP code
def verify_totp(username, totp_uc):
    conn = LDBConn()
    cursor = conn.cursor()
    cursor.execute('SELECT totp_secret FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        totp_enc = result[0]
        crypt_suite = Fernet(generate_fernet_key(username))
        totp_secret = crypt_suite.decrypt(totp_enc).decode()
        totp = pyotp.TOTP(totp_secret)
        return totp.verify(totp_uc)
    return False


# HACK: Remove the comment of the set_lockout function

# Main function to run the ESDS system
# noinspection PyArgumentList
def run_esds(incog):
    print(Back.RED + "<<SCP FOUNDATION DATABASE ACCESS TERMINAL EMERGENCY SELF DESTRUCT SYSTEM>>")
    print(Fore.CYAN + "WELCOME, PLEASE PROCEED BY ANSWERING THE SECURITY QUESTION")

    # Check ESDS credentials
    sec = math_question(incog)
    while True:
        if not sec:
            os.system("cls")
            print(Back.RED + "<<SCP FOUNDATION DATABASE ACCESS TERMINAL EMERGENCY SELF DESTRUCT SYSTEM>>")
            print(Fore.CYAN + "WELCOME, PLEASE PROCEED BY ANSWERING THE SECURITY QUESTION")
            print("WRONG ANSWER - TRY AGAIN")
            sec = math_question(incog)
        else:
            break
    print(Fore.CYAN + "CORRECT ANSWER - PLEASE CONTINUE BY ENTERING CREDENTIALS")
    con = check_esds_creds(incog)
    if con:
        print(Fore.RED + "WARNING!!! CORRECT CREDENTIALS ENTERED. YOU HAVE ONE LAST CHANCE TO STOP BEFORE THE SYSTEM GOES INTO EFFECT")
        sure = input("DO YOU REALLY WANT TO CONTINUE --> Y/N: ")
        if sure.lower() == "y":
            print("CONFIRMED")
            # Remove specified directories
            print("STEP 1 - Removing modules and clearing logs...")
            shutil.rmtree("modules", True)
            shutil.rmtree("Activity Logs", True)
            # Drop the users table from the database
            print("STEP 2 - Removing users from DATABASE...")
            conn = GDBConn
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            # Corrupt the CSV file
            print("STEP 3 - Now corrupting SCP DATA")
            corrupt_file("scp6999.csv")
            conn.commit()
            conn.close()
            # Ask if the user wants to delete the CCs folder
            cc = input("DO YOU WANT TO DELETE THE CCs FOLDER -> Y/N: ")
            if cc.lower() == "y":
                print("\rADDITIONAL STEP - Removing CCs folder...")
                shutil.rmtree("CCs", True)
            # Set lockout
            print("LAST STEP - Enabling undisableable lockout on system...")
            set_lockout(1, 0)
            print("TERMINATING TERMINAL...")
            time.sleep(3)
            exit()
        print(Back.RED + "<<OPERATION CANCELED>>")
        chronicle_log("<<ESDS OPERATION CANCELLED>>", incog)
    else:
        print("WRONG CREDENTIALS! ENABLING IMMEDIATE LOCKOUT")
        chronicle_log("<<TERMINAL AUTOMATIC LOCKOUT INITIATED>>", incog)
        # set_lockout(1, 1)
        anim("TERMINATING TERMINAL...", "DONE", 15)
        time.sleep(3)
        exit()
