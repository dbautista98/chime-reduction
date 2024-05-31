# imports
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pytz 

from datetime import datetime, timezone, timedelta
from scipy.optimize import curve_fit


def gaussian(x, height, center, width, baseline):
    return height * np.exp( -(x - center)**2 / (2*width)**2) + baseline

def gauss_fit_peak(data_grid, freq_array, target_freq, flux, debug=False, matched_index=1900):
    index = np.argmin(np.abs(target_freq - freq_array))
    lower = matched_index - 300
    upper = matched_index + 300
    freq_slice = data_grid[lower:upper, index]
    xx = np.arange(lower, upper)
    coeff, cov = curve_fit(gaussian, xx, freq_slice, p0=(1e8, matched_index, 10, 1e7))
    height, center, width, baseline = coeff
    counts_to_flux = flux / height
    calibrated_grid = data_grid * counts_to_flux

    ## ======================= DEBUG =======================
    if debug:
        fig, axs = plt.subplots(2)
        axs[0].plot(xx, freq_slice, label="raw counts")
        axs[0].plot(xx, gaussian(xx, *coeff), label="fitted gaussian")
        axs[0].hlines(0, lower, upper, label="zero", color="black")
        axs[0].hlines(baseline, lower, upper, label="baseline counts", color='red')
        axs[0].legend(fontsize=7)
        axs[0].set_xlim(lower, upper)
        axs[0].set_ylabel("power [counts]")

        refit, cov = curve_fit(gaussian, xx,  calibrated_grid[lower:upper, index], p0=(800000, matched_index, 10, 1e5))
        
        axs[1].plot(xx, calibrated_grid[lower:upper, index], label="calibrated data")
        axs[1].hlines(flux, lower, upper, label="given flux", color="black")
        axs[1].hlines(refit[0], lower, upper, label="fitted flux", color="red", linestyle="dashed")
        axs[1].hlines(refit[0] + refit[-1], lower, upper, label="given flux + baseline", color="orange", linestyle="dashed")
        axs[1].plot(xx, gaussian(xx, *refit), label="refitted gaussian")
        axs[1].hlines(refit[-1], lower, upper, label="baseline flux", color='red')
        axs[1].legend(fontsize=7)
        axs[1].set_xlim(lower, upper)
        axs[1].set_ylabel("calibrated flux [Jy]")

        fig.savefig("test.png", bbox_inches="tight", transparent=False)
        plt.close()
    ## ======================= END DEBUG =======================

    return calibrated_grid

def load_CHIME_data(data_dir):
    files = glob.glob(f"{data_dir}/*npy")
    files.sort()
    data_path, end_path, start_path = files
    CHIME_data = np.load(data_path, allow_pickle=True)
    start_data = np.load(start_path, allow_pickle=True)
    end_data = np.load(end_path, allow_pickle=True)
    start_time = start_data[()].astimezone(timezone.utc)
    end_time = end_data[()].astimezone(timezone.utc)

    frequency = np.linspace(400, 800, num=1024) # frequency in MHz

    dt = (end_time - start_time).seconds / CHIME_data.shape[0]
    timestamps = [start_time + timedelta(seconds=dt*i) for i in range(len(CHIME_data))]
    return CHIME_data, frequency, timestamps

def load_Learmonth_data(data):
    UT_time, f_245, f_410, f_610, f_1415, f_2695, f_4975, f_8800, f_15400 = np.loadtxt(data, delimiter=" ", unpack=True, dtype=str)
    freqs = [f_245, f_410, f_610, f_1415, f_2695, f_4975, f_8800, f_15400]
    for i in range(len(freqs)):
        mask = np.where(freqs[i] == "//////")
        freqs[i][mask] = np.nan
        freqs[i] = freqs[i].astype(np.float32)
    f_245, f_410, f_610, f_1415, f_2695, f_4975, f_8800, f_15400 = [freq for freq in freqs]

    date_str = os.path.basename(data)[1:-4]
    date_format = "%y%m%d"
    date_time_list = []
    seconds_list = []
    for i in range(len(UT_time)):
        time_str = UT_time[i]
        time_format = "%H%M%S"
        date_time_str = f"{date_str}{time_str}"
        date_time_format = f"{date_format}{time_format}"
        date_time_object = datetime.strptime(date_time_str, date_time_format).replace(tzinfo=pytz.UTC)
        date_time_list.append(date_time_object)
        seconds_list.append(float(date_time_object.strftime("%H"))*60*60 + float(date_time_object.strftime("%M"))*60 + float(date_time_object.strftime("%S")))

    data_dict = {"time":date_time_list, "seconds":seconds_list, "245":f_245, "410":f_410, "610":f_610, "1415":f_1415, "2695":f_2695, "4975":f_4975, "8800":f_8800, "15400":f_15400}
    df = pd.DataFrame(data_dict)
    return df

def angular_separation(az1, el1, az2, el2, deg=True):
    """
    equations pulled from: 
    https://www.atnf.csiro.au/people/Tobias.Westmeier/tools_separation.php
    https://www.atnf.csiro.au/people/Tobias.Westmeier/tools_spherical.php#separation
    """

    if deg:
        az1 = az1 * np.pi/180
        el1 = el1 * np.pi/180
        az2 = az2 * np.pi/180
        el2 = el2 * np.pi/180
    cos_a = np.sin(el1)*np.sin(el2) + np.cos(el1)*np.cos(el2)*np.cos(az1 - az2)
    a = np.arccos(cos_a)
    return a

def match_times(min_separation_time, timestamps, timezone=-4):
    time_separation = []
    timestamps = timestamps.copy()
    min_hour = int(min_separation_time.split(":")[0])
    min_minute = int(min_separation_time.split(":")[1])

    for i in range(len(timestamps)):
        timestamps[i] = timestamps[i] + timedelta(hours=int(timezone)) # convert from UTC to timezone of solar position data
        time_separation.append(np.abs((timestamps[i].hour - min_hour) * 60 + (timestamps[i].minute - min_minute)))

    closest_approach_index = np.argmin(time_separation)

    return closest_approach_index

def get_closest_position(sun_positions, data_timestamps, target_azimuth=305.3, target_elevation=59.9129, deg=True):
    """
    default azimuth and elevation are the best fit pointing for CHIME at GBO
    """

    separation = angular_separation(sun_positions["azimuth"].values,
                                    sun_positions["altitude"].values, 
                                    target_azimuth,
                                    target_elevation, 
                                    deg=deg)
    
    min_index = np.argmin(separation)
    min_separation_time = sun_positions.iloc[min_index]["time"]
    timezone = sun_positions.iloc[min_index]["time_zone"]

    matched_index = match_times(min_separation_time, data_timestamps, timezone=timezone)

    return matched_index

def normal_vector(phi, theta, degrees=True):
    if degrees:
        phi = phi * np.pi / 180
        theta = theta * np.pi / 180
    
    x = np.cos(phi)*np.cos(theta)
    y = np.sin(phi)*np.cos(theta)
    z = np.sin(theta)

    return np.array([x, y, z])

def reduce_learmonth_data(df, tolerance=10, key="410"):
    mask = np.where(np.abs(df[key].values - np.nanmedian(df[key])) < tolerance)
    sun_track = df.iloc[mask]

    return sun_track
