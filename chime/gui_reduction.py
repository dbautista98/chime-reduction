# if calibration fails due to a TV channel appearing at 
# 610 MHz, switch down to 410 MHz for calibration

import os
import numpy as np
from datetime import datetime
import pandas as pd
import glob
import argparse

# CHIME package imports
import calibration
import util

def write_csv(data_path, outdir=".", log=False, logdir="."):
    date = data_path.split("/")[-2]
    data_grid, frequency, timestamps = calibration.load_CHIME_data(data_path, unit="MHz")
    start_time = timestamps[0]

    if log:
        util.check_dir(outdir+"/plots/")

    data_grid = calibration.calibration(data_path, 
                                        target_freq=410,
                                        target_flux=calibration.median_410,
                                        debug=True, 
                                        outdir=outdir+"/plots/", 
                                        filename="debug",
                                        log=log,
                                        logdir=logdir)

    obs_time = start_time.strftime("%Y-%m-%dT%H:%M:%S%:z")
    mean_spectrum = np.round(np.nanmean(data_grid, axis=0), decimals=3)
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

    util.check_dir(f"{outdir}/{date}/")
    df.to_csv(f"{outdir}/{date}/{date}.csv", index=False)
    print(f"written to {outdir}/{date}/{date}.csv")
    return 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="a script to calibrate a day of CHIME data and average it down to a single spectrum")
    parser.add_argument("-indir", "-i", help="directory input data lives", default=os.getcwd())
    parser.add_argument("-outdir", "-o", help="directory where output data goes", default=os.getcwd())
    parser.add_argument("-noplot", "-n", help="specify not to generate diagnostic plot", default=True, action="store_false")
    args = parser.parse_args()

    data_dir = args.indir
    outdir = args.outdir
    util.check_dir(outdir)

    dirs = glob.glob(f"{data_dir}/202*_*/")
    try:
        dirs.remove("__pycache__/")
    except Exception:
        pass

    for date in dirs:
        this_day = date.split("/")[-2]
        if os.path.exists(f"{outdir}/{this_day}/{this_day}.csv"):
            pass
        else:
            write_csv(date, outdir=outdir, log=args.noplot)
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")        
