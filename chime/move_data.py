import glob
import shutil
import os
from datetime import datetime

# CHIME package imports
try:
    from . import util
except:
    import util

def move_data():
    """
    This is a driver function to move the data from the landing directory to the ESM 
    archive on lustre. It will check if the file is already written to lustre. If the 
    file is already there, it will delete the duplicate file in the landing directory. 
    If that file has not yet been written to lustre, this function will move the file. 

    The end result is a landing directory that contains no CHIME data. 
    """
    all_dirs = glob.glob("202*_*/")
    data_dir = "/lustre/cv/projects/ESM/CHIME_data/"
    try:
        all_dirs.remove("__pycache__/")
    except Exception:
        pass

    if len(all_dirs) == 0:
        print("ERROR:: no data found")

    for date in all_dirs:
        util.check_dir(f"{data_dir}/{date}")

        contents = glob.glob(f"{date}/*")

        for file in contents:
            if os.path.exists(f"{data_dir}{file}"):
                # print(f"FOUND: {data_dir}{file}")
                os.remove(file)
            else:
                shutil.move(file,f"{data_dir}/{file}")
                # print(f"MISSING: {data_dir}{file}")
                print(f"moved {file} to {data_dir}/{file}")
                # print()

        os.rmdir(date)

if __name__ == "__main__":
    move_data()
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
