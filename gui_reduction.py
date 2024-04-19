import os
import numpy as np
from datetime import datetime, timezone, timedelta
import pandas as pd
import glob

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
    

def write_csv(data_path, start_path, outdir="./"):
    date = get_date(data_path)
    data_grid, frequency = load_data(data_path)

    start_data = np.load(start_path, allow_pickle=True)
    start_time = start_data[()]

    datetime = [start_time] * 1024
    mean_spectrum = np.nanmean(data_grid, axis=0)

    data_dict = {"datetime":datetime, "intensity":mean_spectrum, "frequency":frequency}
    df = pd.DataFrame(data_dict)

    check_dir(f"{outdir}/{date}/")
    df.to_csv(f"{outdir}/{date}/{date}.csv", index=False)
    return 

if __name__ == "__main__":
    dirs = glob.glob("*_*/")
    try:
        dirs.remove("__pycache__/")
    except Exception:
        pass

    outdir = "/home/scratch/dbautist/CHIME_backup/"

    for date in dirs:
        if os.path.exists(f"{outdir}/{date}/{date}.csv"):
            pass
        else:
            contents = glob.glob(date + "/*npy")
            contents.sort()
            write_csv(contents[0], contents[2], outdir=outdir)
            
