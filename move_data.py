import glob
import shutil
import os
from datetime import datetime

def check_dir(filepath):
    if os.path.exists(filepath):
        return
    else:
        os.mkdir(filepath)
        return


def move_data():
    all_dirs = glob.glob("*_*/")
    data_dir = "/lustre/cv/projects/ESM/CHIME_data/"
    try:
        all_dirs.remove("__pycache__/")
    except Exception:
        pass
    
    if len(all_dirs) == 0:
        print("ERROR:: no data found")

    for date in all_dirs:
        check_dir(f"{data_dir}/{date}")

        contents = glob.glob(f"{date}/*")

        for file in contents:
            if os.path.exists(f"{data_dir}{file}"):
                # print(f"FOUND: {data_dir}{file}")
                os.remove(file)
            else:
                shutil.move(file,f"{data_dir}{file}")
                # print(f"MISSING: {data_dir}{file}")
                print(f"moved {file} to {data_dir}{file}")
                # print()
        
        os.rmdir(date)

if __name__ == "__main__":
    move_data()
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
