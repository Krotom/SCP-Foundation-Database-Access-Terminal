import os
import sys
import shutil
import datetime

if not os.path.exists("Activity Logs"):
    os.mkdir("Activity Logs")

date = datetime.datetime.now().strftime("%h:%H:%M:%S")
act_log = str(date).replace(":", "-") + "-Log.txt"
folder = "Activity Logs"
save_path = os.path.join(folder, act_log)


def chronicle_log(write, incog):
    if not incog:  # REM: Replace with 'not incog' after development
        print("Logging functtions currently down for development, writing to console instead: " + write)
        #    try:
        #        with open(save_path, 'a', encoding="utf-8") as f:
        #            f.write(write)
        #    except FileNotFoundError:
        #        pass


def clean_slate():
    mydir = "Activity Logs"
    try:
        shutil.rmtree(mydir)
    except Exception as e:
        print(f"An error happened while trying to delete logs: {e}")


if __name__ == '__main__':
    print("This file includes necessary logging functions of the terminal, it will not do what you want this way...")
    input("Press enter to terminate...")
