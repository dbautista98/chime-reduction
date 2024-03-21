import glob
import os
from datetime import datetime, timezone, timedelta
import shutil
import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u

def check_dir(filepath):
    if os.path.exists(filepath):
        return
    else:
        os.mkdir(filepath)
        return

def already_exists(filepath):
    return os.path.exists(filepath)

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

def plot_waterfall(data_path, start_path, end_path, outdir="./"):
    CHIME_data = np.load(data_path, allow_pickle=True)
    start_data = np.load(start_path, allow_pickle=True)
    end_data = np.load(end_path, allow_pickle=True)
    start_time = start_data[()].astimezone(timezone.utc)
    end_time = end_data[()].astimezone(timezone.utc)

    frequency = np.linspace(400e6, 800e6, num=1024)*u.Hz
    frequency = frequency.to(u.MHz).value

    dt = (end_time - start_time).seconds / CHIME_data.shape[0]
    timestamps = [start_time + timedelta(seconds=dt*i) for i in range(len(CHIME_data))]

    time_series = np.sum(CHIME_data, axis=1)
    average_spectrum = np.mean(CHIME_data, axis=0)

    extent = [frequency.min(), frequency.max(), min(timestamps), max(timestamps)]

    fig = plt.figure(figsize=(10,10))
    gs = fig.add_gridspec(2,2, hspace=0.02, wspace=0.03, width_ratios=[3,1], height_ratios=[1,3])
    (ax1, ax2), (ax3, ax4) = gs.subplots(sharex="col", sharey="row")
    ax1.set_title(f"GBO CHIME outrigger data\n{start_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")} to {end_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")}")
    ax1.semilogy(frequency, average_spectrum, color="black", linewidth=1)
    ax1.set_ylabel("average power [counts]")
    ax2.set_visible(not ax2)
    ax3.imshow(CHIME_data, aspect="auto", extent=extent, vmin=0, vmax=4e7)
    ax3.set_xlabel("Frequency [MHz]")
    ax3.set_ylabel("UTC time (mm-dd hh)")
    ax4.plot(time_series[::-1], timestamps, color="black", linewidth=1)
    ax4.set_xlabel("integrated power\n[counts]")
    plt.savefig(f"{outdir}/{start_time.strftime('%Y_%j')}_waterfall.png", bbox_inches="tight", transparent=False)
    print(f"saved plot to: {outdir}/{start_time.strftime('%Y_%j')}_waterfall.png")
    plt.close()

def move_files():
    all_files = glob.glob("*npy")

    data_dir = "/users/dbautist/CHIME_landing_directory/"

    for file in all_files:
        this_date = get_date(file)
        check_dir(data_dir + this_date)
        if already_exists(data_dir + this_date + "/" + file):
            os.remove(file)
        else:
            print(f"moved {file} to {data_dir}{this_date}/{file}")
            shutil.move(file, data_dir + this_date + "/" + file)

def make_waterfalls():
    dirs = glob.glob("*_*/")
    try:
        dirs.remove("__pycache__/")
    except Exception:
        pass

    for date in dirs:
        if os.path.exists(f"{date}/{date.replace("/", "")}_waterfall.png"):
            pass
        else:
            contents = glob.glob(date + "/*npy")
            contents.sort()
            plot_waterfall(contents[0], contents[2], contents[1], outdir=f"{date}/")

if __name__ == "__main__":
    move_files()
    make_waterfalls()
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
