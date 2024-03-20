import glob
import os
from datetime import datetime
import shutil

def check_dir(filepath):
    if os.path.exists(filepath):
        return
    else:
        os.mkdir(filepath)
        return

def already_exists(filepath):
    return os.path.exists(filepath)

def get_date(filepath):
    start_date = filepath.split("_")[2]
    time_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
    YYYY_DD = time_obj.strftime("%Y_%j")
    return YYYY_DD

def move_files():
    all_files = glob.glob("*npy")

    data_dir = "/lustre/cv/projects/ESM/CHIME_data/"

    for file in all_files:
        this_date = get_date(file)
        check_dir(data_dir + this_date)
        if already_exists(data_dir + this_date + "/" + file):
            os.remove(file)
        else:
            print(f"moved {file} to {data_dir}{this_date}/{file}")
            shutil.move(file, data_dir + this_date + "/" + file)

if __name__ == "__main__":
    move_files()
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
