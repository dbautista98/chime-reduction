import os
import numpy as np
from datetime import datetime, timezone, timedelta
import pandas as pd
import glob
import calibration

def load_data(data_path):
    CHIME_data = np.load(data_path, allow_pickle=True)
    
    df = -0.390625
    frequency = np.arange(800, 400, df)[::-1]

    return CHIME_data, frequency*1e6

def get_date(filepath):
    """
    The filepath of the .npy files have the
    timestamps recorded in UTC, whereas the 
    timestamps inside the file are converted 
    to ET and need to be moved back to UTC
    """
    filename = os.path.basename(filepath)
    start_date = filename.split("_")[2]
    time_UTC  = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
    YYYY_DD = time_UTC.strftime("%Y_%j")
    return YYYY_DD

def check_dir(filepath):
    if os.path.exists(filepath):
        return
    else:
        os.mkdir(filepath)
        return

def write_csv(data_path, outdir="."):
    date = data_path.split("/")[-2]
    contents = glob.glob(date + "/*npy")
    contents.sort()

    data_grid, frequency = load_data(contents[0])
    data_grid = calibration.calibration(data_path, debug=True, outdir=outdir+"/plots/", filename="debug")

    start_data = np.load(contents[2], allow_pickle=True)
    start_time = start_data[()]

    datetime = [start_time] * 1024
    mean_spectrum = np.nanmean(data_grid, axis=0)

    data_dict = {"datetime":datetime, "intensity":mean_spectrum, "frequency":frequency}
    df = pd.DataFrame(data_dict)

    check_dir(f"{outdir}/{date}/")
    df.to_csv(f"{outdir}/{date}/{date}.csv", index=False)
    print(f"written to {outdir}/{date}/{date}.csv")
    return 

if __name__ == "__main__":
    dirs = glob.glob("*_*/")
    try:
        dirs.remove("__pycache__/")
    except Exception:
        pass

    outdir = "/home/scratch/dbautist/TEST/610/"#"/home/scratch/dbautist/CHIME_backup/"

    for date in dirs:
        this_day = date.split("/")[-2]
        if os.path.exists(f"{outdir}/{this_day}/{this_day}.csv"):
            pass
        else:
            write_csv(date, outdir=outdir)
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")        
