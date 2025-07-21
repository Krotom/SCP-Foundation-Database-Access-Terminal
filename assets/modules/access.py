import os
from time import sleep as sl
import requests
import pandas as pd
import zipfile
import csv
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

from modules.authSys import check_for_notices
from modules.animations import anim, access_anim
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from modules.chronicle_engine import chronicle_log

# Database URL
io_addr = "krotom.github.io/archive.zip"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Check and download the dataset if not present
def check_dataset():
    global db_deactive
    if not os.path.exists("scp6999.csv"):
        try:
            print("SCP Database not found! Automatically reinstalling...")
            chronicle_log("<<DATASET AUTO RE-INSTALL>>", False)
            with open("archive.zip", 'wb') as file:
                resp = requests.get(io_addr, verify=False)
                resp.raise_for_status()
                file.write(resp.content)
            with zipfile.ZipFile('archive.zip') as zipp:
                zipp.extractall()
            os.remove("archive.zip")
            db_deactive = False
            return True
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while downloading the dataset: {e}")
        except Exception as e:
            print(f"An error happened, access to database is now deactivated: {e}")
            chronicle_log("Access to Database is now revoked due to an update error", False)
            print(f"An unexpected error occurred: {e}")
        finally:
            if os.path.exists("archive.zip"):
                os.remove("archive.zip")
            db_deactive = True
            return False
    else:
        db_deactive = False
        return True


# Update the dataset
def update_dataset(inc):
    try:
        print("Checking for updates...")
        with open("archive.zip", 'wb') as file:
            resp = requests.get(io_addr)
            file.write(resp.content)
        with zipfile.ZipFile('archive.zip') as zipp:
            zipp.extractall()
        os.remove("archive.zip")
        print(f"{Fore.GREEN}Dataset updated successfully.")
        chronicle_log("<<DATASET UPDATED>>", inc)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the dataset: {e}")
        chronicle_log("<<MANUAL DATASET UPDATE FAILED>>", inc)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        chronicle_log("<<MANUAL DATASET UPDATE FAILED>>", inc)
    finally:
        if os.path.exists("archive.zip"):
            os.remove("archive.zip")


if not __name__ == '__main__':
    ok = check_dataset()
    if ok:
        dt = pd.read_csv("scp6999.csv")
        data = dt.copy()
    else:
        db_deactive = True


# Access SCP data by SCP number
def access(no, retry_count=3, retry_delay=2):
    global db_deactive
    if 'db_deactive' not in globals():
        db_deactive = False

    if db_deactive:
        print("The Database is currently unavailable")
        return

    if no.lower().startswith("scp-"):
        scp = no.upper()
    else:
        scp = "SCP-" + str(no)

    for attempt in range(retry_count):
        access_anim(f"{Fore.GREEN}ACCESS GRANTED{Fore.RESET}", 10)
        anim("Decoding file...", "COMPLETE", 10)
        anim("Loading file...", "LOADED", 20)
        try:
            print(f"\nSCP NO.: {data[data['code'] == scp]['code'].iloc[0]}")
            print(f"SCP Title: {data[data['code'] == scp]['title'].iloc[0]}")
            print(f"Current file state: {data[data['code'] == scp]['state'].iloc[0]}")
            cfn = check_for_notices(scp)
            if cfn is not None:
                try:
                    for i in cfn[0]:
                        if i is not None:
                            print(i)
                except Exception:
                    pass
            print(f"\n\n{data[data['code'] == scp]['text'].iloc[0]}")
            return
        except Exception as ex:
            print(f"\rError while trying to load file (Attempt {attempt + 1}/{retry_count})...")
            print(f"Error code: {ex}")
            sl(retry_delay)

    print("Failed to access the database after multiple attempts")


def export_scp(no, file_format):
    global db_deactive
    if 'db_deactive' not in globals():
        db_deactive = False

    if db_deactive:
        print("The Database is currently unavailable")
        return

    if no.lower().startswith("scp-"):
        no = no.upper()
    else:
        no = "SCP-" + str(no)

    for attempt in range(3):
        try:
            # Fetch SCP data from the dataframe based on SCP number
            scp_data = data[data['code'] == no]

            # If SCP data is not found, print an error message
            if scp_data.empty:
                print(f"SCP-{no} not found in the Database.")
                return

            # Define SCP field names based on the CSV format
            field_names = ["code", "title", "text", "image captions", "rating", "state", "tags", "link"]

            # Convert SCP data to a dictionary
            scp_dict = scp_data.iloc[0].to_dict()

            # File name based on SCP number and file format
            file_name = f"{no}.{file_format.lower()}"

            # Export SCP data based on the specified file format
            if file_format.lower() == "csv":
                with open(file_name, mode='w', newline='') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=field_names)
                    writer.writeheader()
                    writer.writerow(scp_dict)
                print(f"SCP-{no} exported to {file_name} successfully.")
                return
            elif file_format.lower() == "json":
                with open(file_name, mode='w') as json_file:
                    json.dump(scp_dict, json_file, indent=4)
                print(f"SCP-{no} exported to {file_name} successfully.")
                return
            elif file_format.lower() == "xml":
                root = ET.Element("scp")
                for key, value in scp_dict.items():
                    child = ET.SubElement(root, key.replace(' ', '_'))
                    child.text = str(value)

                # Pretty print the XML
                xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

                with open(file_name, mode='w') as xml_file:
                    xml_file.write(xml_str)
                print(f"SCP-{no} exported to {file_name} successfully.")
                return
            else:
                print("Unsupported file format. Please use CSV, JSON, or XML.")
                return
        except Exception as e:
            print(f"An error happened while exporting SCP (Attempt {attempt + 1}/3")
            print(f"Error: {e}")


# Search SCP database by keyword
def search(cmmd, incognito):
    keyword = " ".join(cmmd[1:])
    results = data[data['text'].str.contains(keyword, case=False, na=False)]
    if results.empty:
        print(Fore.RED + "No results found for your search.")
        chronicle_log(f"No results found for keyword: {keyword}", incognito)
    else:
        cnt = 0
        for idx, row in results.iterrows():
            print(Fore.GREEN + f"\n{row['code']}: {row['title']}\n" + Style.RESET_ALL)
            print(f"{Fore.YELLOW}Status: {Fore.CYAN}{row['state']}\n")
            print(f"{Fore.YELLOW}Description: {Fore.CYAN}{row['text'][:200]}...\n")
            print(f"{Fore.MAGENTA}Access full entry with: access {row['code']}\n")
            cnt += 1
        chronicle_log(f"Database search for keyword: {keyword}, {cnt} results found", incognito)


if __name__ == '__main__':
    print("This file includes necessary database access functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
