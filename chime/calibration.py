# imports
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pytz 
from astropy import units as u
import astropy.coordinates as coord
from astropy.time import Time

from datetime import datetime, timezone, timedelta
from scipy.optimize import curve_fit

# TODO:
# - remove hardcoded filepaths from calibration function (sunPosition specifically)

#### CHIME definitions
CHIME_azimuth  = 305.3 # degrees
CHIME_altitude = 59.9129 # degrees: with zenith = 90 and nadir = -90

CHIME_latitude = 38.433056  # earth latitude  in degrees
CHIME_longitude= -79.839722 # earth longitude in degrees 

median_410 = 49 * 1e4 # median solar flux at 410 MHz in Jy
median_610 = 75 * 1e4 # median solar flux at 610 MHz in Jy
sd_410 = 8.88 * 1e4  # standard deviation of solar flux at 410 MHz in Jy
sd_610 = 10.11 * 1e4   # standard deviation of solar flux at 610 MHz in Jy

def gaussian(x, height, center, width, baseline):
    """
    Define a gaussian function specified by height, center
    width, and baseline. The gaussian takes the form:

    y = height * exp( -0.5 * (x - center)**2 / width**2 ) + baseline

    Arguments:
    ---------------
    x : numpy.ndarray
        The x values for which gaussian will reutrn values
    height : float
        The amplitude of the gaussian
    center : float
        The center (mean) of the gaussian
    width : float
        The standard deviation of the gaussian
    baseline : float
        The baseline offset from zert of the gaussian.

    Returns:
    ---------------
    y : numpy.ndarray
        The value of the gaussian for the provided inputs
    """
    return height * np.exp( -0.5*(x - center)**2 / (width**2)) + baseline

def gauss_fit_peak(data_grid, freq_array, target_freq, flux, debug=False, matched_index=1900, outdir=".", filename='test'):
    """
    Calibrate the provided data by fitting a gaussian to signal of the sun passing
    through the CHIME beam. These fit coefficients, along with a known flux value
    of the sun will be used to derive a conversion factor to convert from counts 
    to Jansky (Jy). 

    Calls `scipy.optimize.curve_fit` to determine best fit parameters
    for a gaussian, based on the provided data

    Arguments:
    ---------------
    data_grid : numpy.ndarray
        The input CHIME data to calibrate. The data shape is 
        expected to be (n_steps,1024)
    freq_array : numpy.ndarray
        The range of frequency values for the CHIME data. The
        data is from 400 - 800 MHz and has 1024 freuency channels
    target_freq : float
        The frequency for which a known flux value of the sun is known 
    flux : float
        The known flux value of the sun. This is used to set the conversion
        from counts to Jy 
    debug : bool
        Option to generate a debug plot showing the gaussian fit on the 
        data. This is useful for visual verification of fit success. 
        The default value is False
    matched_index : int
        The estimated timestamp index that the sun passes through the CHIME
        beam. Based on how the data is saved, 1900 serves as a good estimate 
        for when the sun passes. Occasionally there will be data that is cut
        differently, which will often require manual re-calibration. 
    outdir : str
        Path to where the debug plot will be saved. The default value 
        is the current working directory
    filename : str
        The name of the debug plot to generate. The default is "test"

    Returns:
    ---------------
    calibrated_grid : numpy.ndarray
        The calibrated array of CHIME data. This data has units of (Jy)
        and has the same shape as the input data_grid
    coeff : numpy.ndarray
        The best fit coefficeints from fitting a gaussian to the signal 
        of the sun passing through CHIME's beam. The order of the coefficients
        is the same as in `gaussian` above: (height, center, width, baseline)
    """
    index = np.argmin(np.abs(target_freq - freq_array))
    lower = max((matched_index - 300, 0))
    upper = min((matched_index + 300, len(data_grid)-1))
    freq_slice = data_grid[lower:upper, index]

    # mask potential rfi in sun 
    mask = np.where(freq_slice < 1e9)
    freq_slice = freq_slice[mask]
    xx = np.linspace(lower, upper, num=len(freq_slice))

    # define guessing parameters
    bounds = ((0,np.min(xx),3,0), (1e9, np.max(xx), 100, np.inf))
    p0=(1e8, matched_index, 10, 1e7)

    # fit gaussian and calibrate based on fit values
    coeff, cov = curve_fit(gaussian, xx, freq_slice, p0=p0, bounds=bounds)
    height, center, width, baseline = coeff
    counts_to_flux = flux / height
    calibrated_grid = data_grid * counts_to_flux

    ## ======================= DEBUG =======================
    if debug:
        fig, axs = plt.subplots(2)
        axs[0].plot(np.arange(lower, upper), data_grid[lower:upper, index], label="raw counts")
        axs[0].plot(xx, gaussian(xx, *coeff), label="fitted gaussian")
        axs[0].hlines(0, lower, upper, label="zero", color="black")
        axs[0].hlines(baseline, lower, upper, label="baseline counts", color='red')
        axs[0].legend(fontsize=7)
        axs[0].set_xlim(lower, upper)
        axs[0].set_ylabel("power [counts]")

        calibrated_slice = calibrated_grid[lower:upper, index]
        calibrated_slice = calibrated_slice[mask]
        bounds = ((0,np.min(xx),3,0), (1e9, np.max(xx), 100, np.inf))
        p0=(800000, matched_index, 10, 1e5)
        refit, cov = curve_fit(gaussian, xx,  calibrated_slice, p0=p0, bounds=bounds)

        axs[1].plot(np.arange(lower, upper), calibrated_grid[lower:upper, index], label="calibrated data")
        axs[1].hlines(flux, lower, upper, label="given flux", color="black")
        axs[1].hlines(refit[0], lower, upper, label="fitted flux", color="red", linestyle="dashed")
        axs[1].hlines(refit[0] + refit[-1], lower, upper, label="given flux + baseline", color="orange", linestyle="dashed")
        axs[1].plot(xx, gaussian(xx, *refit), label="refitted gaussian")
        axs[1].hlines(refit[-1], lower, upper, label="baseline flux", color='red')
        axs[1].legend(fontsize=7)
        axs[1].set_xlim(lower, upper)
        axs[1].set_ylabel("calibrated flux [Jy]")

        fig.savefig(f"{outdir}/{filename}.png", bbox_inches="tight", transparent=False)
        plt.close()
    ## ======================= END DEBUG =======================

    return calibrated_grid, coeff

def load_CHIME_data(data_dir, unit="MHz"):
    """
    Read in the CHIME data after it has been organized by make_waterfalls.move_files
    This function takes in the parent directory (eg: /path/to/directory/2026_001) 
    and returns three objects: the data array-- shape: (nint, 1024; the frequency axixs, 
    and the timestamps for each integration. 

    Arguments:
    ---------------
    data_dir : str
        The file path to the parent directory, as created by `make_waterfalls.move_files`
        The parent directory is the name of the date of observation, with the 
        format %Y_%j (eg: 2026_001 for January 1, 2026). An example path 
        is (/path/to/directory/2026_001)
    unit : str
        The unit to return the frequency axis. The options are {Hz, MHz} and the
        default is MHz 

    Returns:
    ---------------
    CHIME_data : numpy.ndarray
        Raw data from a day of CHIME data, as provided by the CHIME 
        team to GBO. The data has shape of (nint, 1024) -- the number of
        time steps, and the number of frequency channels
    frequency : numpy.ndarray
        The frequency axis of the CHIME data. The native CHIME frequency range
        is 400 - 800 MHz, and is split into 1024 channels. This data has a 
        frequency resolution of 390.625 kHz. 
    timestamps : list of datetime.datetime
        The timestamps in UTC for each integration of the retreived data. The 
        timestamps are ordered such that the first entry is the start of the 
        data and the last timestamp is the end of the observtion. The time 
        resolution is ~30 seconds. 
    """
    files = glob.glob(f"{data_dir}/*npy")
    files.sort()
    data_path, end_path, start_path = files
    CHIME_data = np.load(data_path, allow_pickle=True)
    start_data = np.load(start_path, allow_pickle=True)
    end_data = np.load(end_path, allow_pickle=True)
    start_time = start_data[()].astimezone(timezone.utc)
    end_time = end_data[()].astimezone(timezone.utc)

    df = -0.390625
    frequency = np.arange(800, 400, df)[::-1] # frequency in MHz

    dt = (end_time - start_time).seconds / CHIME_data.shape[0]
    timestamps = [start_time + timedelta(seconds=dt*i) for i in range(len(CHIME_data))]

    if unit == "MHz":
        frequency = frequency
    if unit == "Hz":
        frequency = frequency * 1e6

    return CHIME_data, frequency, timestamps

def load_Learmonth_data(data):
    """
    Load a day of data collected by Learmonth Solar Observatory in Australia. LSO
    collects data over a range of frequencies, and the data that is most interesting
    for CHIME are at 410 and 610 MHz. These overlap with CHIME's sensitivity range and 
    can be used for calibrating the data. 
    This function returns a pandas DataFrame with columns for the timestamp and 
    frequency of observation. 

    Arguments:
    ---------------
    data : str
        Filepath to the learmonth .SRD file for a single day

    Returns:
    ---------------
    learmonth_df : pandas.core.frame.DataFrame
        The pandas DataFrame containing the Learmonth data from the 
        provided data
    """
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
    Calculate the angular separation of two points on a unit sphere

    equations pulled from: 
    https://www.atnf.csiro.au/people/Tobias.Westmeier/tools_separation.php
    https://www.atnf.csiro.au/people/Tobias.Westmeier/tools_spherical.php#separation

    Arguments:
    ---------------
    az1 : numpy.ndarray
        Azimuth coordinate of target one to compare. This is numpy array compatible. 
    el1 : numpy.ndarray
        Elevation coordinate of target one to compare. This is numpy array compatible. 
    az2 : float
        Azimuth coordinate of target two to compare
    el2 : float
        Elevation coordinate of target two to compare
    deg : bool
        flag indicating that the data is in units of degrees

    Returns:
    ---------------
    angle : numpy.ndarray
        The angular separation in radians. This is numpy array compatible. 
    """

    if deg:
        az1 = az1 * np.pi/180
        el1 = el1 * np.pi/180
        az2 = az2 * np.pi/180
        el2 = el2 * np.pi/180
    cos_a = np.sin(el1)*np.sin(el2) + np.cos(el1)*np.cos(el2)*np.cos(az1 - az2)
    a = np.abs(np.arccos(cos_a))
    return a

def match_times(min_separation_time, timestamps, timezone=-4):
    """
    Takes a time of day (hh:mm) and the array of CHIME integration timestamps
    and finds the index for the closest CHIME timestamp

    Arguments:
    ---------------
    min_separation_time : str   
        The timestamp (hh:mm in local time) for which the sun was at its closest to 
        the main beam of CHIME. Example timestamp is ("15:55")
    timestamps : list of datetime.datetime
        The timestamps in UTC for each integration of the retreived data. The 
        timestamps are ordered such that the first entry is the start of the 
        data and the last timestamp is the end of the observtion. The time 
        resolution is ~30 seconds. 
    timezone : int
        Time zone separation from UTC. The default is -4 (EDT)

    Returns:
    ---------------
    closest_approach_index : int
        The index of the timestamp that is closest to the provided timestamp
    """
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
    Takes in a pandas DataFrame of the suns position vs time, the timestamps of the 
    CHIME data, and the AZ/EL of CHIME's main beam. default azimuth and elevation are 
    the pointing of CHIME's main beam at GBO. Uses these data to find the index for 
    the sun's closest approach to the CHIME beam. 

    Arguments:
    ---------------
    sun_positions : pandas.core.frame.DataFrame
        A DataFrame containing the time and AZ/EL of the sun over the course of a
        day. 
    data_timestamps : list of datetime.datetime
        The timestamps for the integrations of the CHIME data
    target_azimuth : float
        The azimuth angle of the target, for which the closest approach should be found. 
        The default azimuth is 305.3 degrees. This was found to be where the main beam
        of CHIME points. 
    target_elevation : float
        The elevation angle of the target, for which the closest approach should be found. 
        The default elevation is 59.9129 degrees. This was found to be where the main beam
        of CHIME points.
    deg : bool
        A flag indicating that the input data has units of degrees. A False indicates 
        that the input data has units of radians. The default is True

    Returns:
    ---------------
    matched_index : int
        The index corresponding to the CHIME timestamp for which the sun had the 
        closest approach. 
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
    """
    Convert a unit vector in spherical coordinates specified by angles phi and 
    theta to cartesian coordinates. 

    Since there is frequent confusion about the definition of phi, theta betweem the 
    physics and math communities, here are the definitions I use for this calculation: 

    phi is the azimuthal angle and runs from 0 to 2 pi radians
    theta is the altitude angle and runs from -pi/2 to pi/2

    Arguments:
    ---------------
    phi : numpy.ndarray 
        The azimuthal angle of the vector. Range: (0, 2 pi) radians
    theta : numpy.ndarray 
        The altitude(elevation) angle of the vector. Range (-pi/2, pi/2) radians
    degrees : bool
        Flag indicating that the input data is in units of degrees. The default is True.

    Returns:
    ---------------
    vector : numpy.ndarray 
        The cartesian coordinates of the vector. (x, y, z), shape: (3,)
    """
    if degrees:
        phi = phi * np.pi / 180
        theta = theta * np.pi / 180

    x = np.cos(phi)*np.cos(theta)
    y = np.sin(phi)*np.cos(theta)
    z = np.sin(theta)

    return np.array([x, y, z])

def solar_position(timestamp, lat=38.433056, lon=-79.839722, unit=u.deg):
    """
    Takes in a list of timestamps and the lat/lon coordinates of a place on earth
    and calculates the alt/az of the sun for each of the provided timestamps. 

    Arguments:
    ---------------
    timestamp : list of datetime.datetime
        The timestamps in UTC for each integration of the retreived data. These are
        used to calculate the sun's position in the sky above the provided coordinates
    lat : float
        The lattitude on earth for which to calculate the sun's position in the sky. The 
        default value is 38.433056; the location of the CHIME antenna at GBO
    lon : float
        The longitude on earth for which to calculate the sun's position in the sky. The 
        default value is -79.839722; the location of the CHIME antenna at GBO
    unit : astropy.units.core.Unit
        The units for which the earth coordinates are provided. These should be some 
        measure of angle. The default is u.deg

    Returns:
    ---------------
    alt : numpy.ndarray
        The calculated altitude angle of the sun in the sky above the provided coordinates
        for the provided timestamps. 
    az : numpy.ndarray
        The calculated azimuth angle of the sun in the sky above the provided coordinates
        for the provided timestamps. 
    """
    loc = coord.EarthLocation(lat=lat * unit,
                              lon=lon * unit)

    t = Time(timestamp, scale="utc")
    altaz = coord.AltAz(location=loc, obstime=t)
    sun = coord.get_sun(t)

    alt = sun.transform_to(altaz).alt.deg
    az =  sun.transform_to(altaz).az.deg
    return alt, az

def calibration(chime_path, target_freq=410, target_flux=49 * 1e4, debug=False, outdir='.', filename='test', log=False, logdir="."):
    """
    Take in the raw CHIME data array, with a known flux (Jy) at a known frequency (MHz) 
    and use the passage of the sun through the CHIME beam to fit a gaussian and use the 
    fit parameters to convert the spectra from counts to Jy. 

    This function can write to a log file the success/failure of calibration, as well as 
    the calibration coefficients.

    Optionally can save debug plot and data to validate performance. 

    Arguments:
    ---------------
    chime_path : str
        The file path to the parent directory, as created by `make_waterfalls.move_files`
        The parent directory is the name of the date of observation, with the 
        format %Y_%j (eg: 2026_001 for January 1, 2026). An example path 
        is (/path/to/directory/2026_001)
    target_freq : float
        The frequency (in Mhz) to apply a known flux value to. The reference frequency 
        for calibration. The default frequency is 410 MHz. 
    target_flux : float
        The flux value (in Jy) corresponding to `target_freq`. The default flux is 49 * 1e4 Jy. 
        This value was inferred as the median flux value based on a large number of LSO data. 
    debug : bool
        Flag indicating that a debug plot will be saved, showing the best fit gaussian to the
        data. The default is False (no debug plot will be saved)
    outdir : str
        The directory path to save the debug plot to. The default directory is the current 
        working directory. If `debug=False`, this variable is unused. 
    filename : str
        The filename for the debug plot. The default filename is "test." If `debug=False`, 
        this variable is unused. 
    log : bool
        Flag indicating that the best fit parameters will be logged to a csv file
        called "calibration_log.csv". The default is False.  
    logdir : str 
        The directory path to save the log file to. The default directory is the current 
        working directory. If `log=False`, this variable is unused.

    Returns:
    ---------------
    calibrated_grid : numpy.ndarray
        The CHIME data array, calibrated to Jy based on the provided frequency and flux 
        values. 
    """
    date = chime_path.split("/")[-2]
    try:
        sun_df = pd.read_csv(f"/users/dbautist/CHIME_landing_directory/sunPosition/{date}_CHIME.csv")
    except:
        solution = "please run: python3 /users/dbautist/CHIME_landing_directory/chime/get_sun_position.py --help"
        raise Exception(f"file not found: /users/dbautist/CHIME_landing_directory/chime/sunPosition/{date}_CHIME.csv\n{solution}")
    data_grid, frequency, timestamps = load_CHIME_data(chime_path)

    matched_index = get_closest_position(sun_df, timestamps)

    sun_alt, sun_az = solar_position(timestamps[matched_index], lat=CHIME_latitude, lon=CHIME_longitude, unit=u.deg)
    sun_vector =   normal_vector(sun_az, sun_alt, degrees=True)
    chime_vector = normal_vector(CHIME_azimuth, CHIME_altitude, degrees=True)

    sun_projection_on_chime = np.dot(sun_vector, chime_vector)

    print(f"calibrating", date)
    try:
        calibrated_grid, coeff = gauss_fit_peak(data_grid, 
                                        frequency, 
                                        target_freq, 
                                        target_flux * sun_projection_on_chime, 
                                        matched_index=matched_index, 
                                        debug=debug,
                                        outdir=outdir,
                                        filename=filename)
        success = True
    except RuntimeError as e:
        if str(e) == "Optimal parameters not found: The maximum number of function evaluations is exceeded.":
            print("failed to fit a gaussian to data. Filling log with bogus values")
            coeff = -9999, -9999, -9999, -9999
            success = False
            calibrated_grid = data_grid
        else:
            print("There was another RunTimeError:")
            print(e)
            raise
    except Exception as err:
        print(err)
        raise 

    if log:
        filename = "calibration_log.csv"
        outpath = f"{logdir}/{filename}"
        height, center, width, baseline = coeff
        if not os.path.exists(outpath):
            header = "date,target_freq,target_flux,height,center,width,baseline,sun_projection,success"
            header = header + "\n"
            with open(outpath, "w") as f:
                f.write(header)
        logger_line = f"{date},{target_freq},{target_flux},{height},{center},{width},{baseline},{sun_projection_on_chime},{success}"
        logger_line = logger_line + "\n"
        with open(outpath, "a") as f:
            f.write(logger_line)

    return calibrated_grid
