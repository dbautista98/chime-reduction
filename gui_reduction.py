# if calibration fails due to a TV channel appearing at 
# 610 MHz, switch down to 410 MHz for calibration

import os
import numpy as np
from datetime import datetime
import pandas as pd
import glob
import calibration

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

def write_csv(data_path, outdir=".", log=False, logdir="."):
    date = data_path.split("/")[-2]
    data_grid, frequency, timestamps = calibration.load_CHIME_data(data_path, unit="MHz")
    start_time = timestamps[0]

    if log:
        check_dir(outdir+"/plots/")

    data_grid = calibration.calibration(data_path, 
                                        target_freq=410,
                                        target_flux=calibration.median_410,
                                        debug=True, 
                                        outdir=outdir+"/plots/", 
                                        filename="debug",
                                        log=log,
                                        logdir=logdir)

    obs_time = start_time.strftime("%Y-%m-%dT%H:%M:%S%:z")
    mean_spectrum = np.nanmean(data_grid, axis=0)
    scan_name = start_time.strftime("%Y-%m-%d")

    data_dict = {"instrument":"chime_gbo",
                 "receiver":"chime",
                 "polarization":"I",
                 "intensity_unit":"Jy",
                 "scan_name":scan_name,
                 "scan_datetime":obs_time, 
                 "frequency":frequency,
                 "intensity":mean_spectrum
                 }
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

    outdir = "/home/scratch/dbautist/TEST/410/"#"/home/scratch/dbautist/CHIME_backup/"

    for date in dirs:
        this_day = date.split("/")[-2]
        if os.path.exists(f"{outdir}/{this_day}/{this_day}.csv"):
            pass
        else:
            write_csv(date, outdir=outdir, log=True)
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")        
