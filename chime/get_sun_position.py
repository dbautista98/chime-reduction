import urllib.request
import pandas as pd
import argparse
import os
from datetime import datetime

def default_filename(day, month, year):
    """
    Takes a day, month, year and converts it to a CHIME standard date. 

    Example:
    default_filename(1,1,2026)
    >>> "2026_001_CHIME"

    Arguments:
    ---------------
    day : str
        The day of the date to convert to CHIME standard format. 
    month : str
        The month of the date to convert to CHIME standard format. 
    year : str
        The year of the date to convert to CHIME standard format. 

    Returns:
    ---------------
    standard_date : str
        The CHIME standard date for the provided calendar date. 
    """
    time_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
    YYYY_DDD = time_obj.strftime("%Y_%j")
    return f"{YYYY_DDD}_CHIME"

def query_website(day, month, year, latitude=38.43, longitude=-79.83, time_zone=-4, filename="default"):
    """
    Query the USNO website for the solar position data for the given date and location. 
    This function returns an intermediate data product,  which is more useful after 
    further scraping such as `get_title_info` or `get_alt_az`

    Arguments:
    ---------------
    day : int
        The day of the date to pull data for. Technically can be either an int or a str. 
    month : int
        The month of the date to pull data for. Technically can be either an int or a str. 
    year : int
        The year of the date to pull data for. Technically can be either an int or a str. 
    latitude : float
        The latitude for which to pull solar position data for. The default value is the 
        latitude of Green Bank. This value is 38.43
    longitude : float
        The longitude for which to pull solar position data for. The default value is the 
        longitude of Green Bank. This value is -79.83
    time_zone : int
        The time zone for which to return the data in. The default value is -4, which 
        indicates EDT. 
    filename : str
        The naming convention for the output file. The standard name is YYYY_DDD_CHIME. 
        Unless otherwise specified, the standard filename will be used. 

    Returns:
    ---------------
    data : str
        The decoded text from the website. This is an intermediate data product. 
    """
    if filename == "default":
        filename = default_filename(day, month, year)
    if time_zone > 0:
        time_zone_sign = 1
    elif time_zone < 0:
        time_zone = -1*time_zone
        time_zone_sign = -1
    else:
        time_zone = 0
        time_zone_sign = 1
    url_str = f"https://aa.usno.navy.mil/calculated/altaz?body=10&date={year}-{month}-{day}&intv_mag=1&lat={latitude}&lon={longitude}&label={filename}&tz={time_zone}&tz_sign={time_zone_sign}&submit=Get+Data"
    print(f"querying: {url_str}")

    page = urllib.request.urlopen(url_str)
    data = page.read().decode("utf-8")

    return data

def dms_to_deg(dms):
    """
    A  helper function to convert data from units of degrees:minutes:seconds to 
    decimal degrees (a single number). This function takes intermediate data and 
    converts it to a more useful form. 

    Arguments:
    ---------------
    dms : str
        The angle in units of degrees, minutes, seconds 

    Returns:
    ---------------
    angle_deg : float
        The angle as a single number
    """
    if dms[0] == "N" or dms[0] == "E":
        direction = 1
    elif dms[0] == "S" or dms[0] == "W":
        direction = -1
    else:
        raise ValueError("I don't know what direction the coordinates are in. They should be N,S,E,W")
    degree, minute = dms.split()[1:3]
    degree = int(degree[:-1])
    minute = int(minute[:-4]) / 60
    return direction * (degree + minute)

def get_title_info(data):
    """
    An intermediate helper function to parse the web data from USNO. This function 
    will return the filename, date, lat_degrees, lon_degrees from a query. 

    Arguments:
    ---------------
    data : str
        The output of `query_website`. It is best to feed the contents directly
        into this function. 

    Returns:
    ---------------
    filename : str
        The name of the output file, to which the queried data will be written. 
    date : str
        The date for which the sun's positions will be queried
    lat_degrees : float
        The latitude of the requested location
    lon_degrees : float
        The longitude of the requested location
    """
    first_row = data.split("</tr>")[0]
    description = first_row.split("<th")[1]
    title_contents = description.split("<br> ")
    filename = title_contents[1].replace("\n","").replace(" ", "")
    date = title_contents[3].replace("\n", "").replace(" " , "")
    lat_dms, lon_dms = title_contents[2].split(";")[:2]
    lon_dms = lon_dms.replace(", ", "")

    lat_degrees = dms_to_deg(lat_dms)
    lon_degrees = dms_to_deg(lon_dms)

    return filename, date, lat_degrees, lon_degrees

def get_alt_az(data, time_zone=-4):
    """
    An intermediate helper function to parse the web data from USNO. This function 
    will return the the altitude, azimuth, and corresponding timestamps and time zone 
    for the sun's position above the requested location. 

    Arguments:
    ---------------
    data : str
        The output of query_website. It is best to feed the contents directly
        into this function.
    time_zone : int
        The time zone for which to return the data in. The default value is -4, which 
        indicates EDT.

    Returns:
    ---------------
    df : pandas.core.frame.DataFrame
        A pandas DataFrame containing the timestamp, time zone, altitude, and azimuth 
        from the queried data
    """
    times = []
    altitude = []
    azimuth = []
    rows = data.split("</tr>")[3:-1]
    for i in range(len(rows)):
        one_row = rows[i].split()[1:]
        if "dropped" in one_row:
            break
        altitude.append(float(one_row[1].replace("<td>", "").replace("</td>", "")[:-1]))
        azimuth.append(float(one_row[2].replace("<td>", "").replace("</td>", "")[:-1]))
        times.append(one_row[0].replace("<td>", "").replace("</td>", ""))

    data_dict = {"time":times, "time_zone":time_zone, "altitude":altitude, "azimuth":azimuth}
    df = pd.DataFrame(data_dict)

    return df

def get_sun_position(day, month, year, latitude=38.43, longitude=-79.83, time_zone=-4, filename="default", save=True, outdir="."):
    """
    The driver function to pull solar position data for a chosen date and location. This
    function will query the USNO website and clean the data, before saving it to a csv file. 
    The csv contents include: time, time_zone, altitude, azimuth, date, latitude_degrees, 
    and longitude_degrees

    Arguments:
    ---------------
    day : int
        The day of the date to pull data for. 
    month : int
        The month of the date to pull data for. 
    year : int
        The year of the date to pull data for. 
    latitude : float
        The latitude for which to pull solar position data for. The default value is the 
        latitude of Green Bank. This value is 38.43
    longitude : float
        The longitude for which to pull solar position data for. The default value is the 
        longitude of Green Bank. This value is -79.83
    time_zone : int
        The time zone for which to return the data in. The default value is -4, which 
        indicates EDT. 
    filename : str
        The naming convention for the output file. The standard name is YYYY_DDD_CHIME. 
        Unless otherwise specified, the standard filename will be used. 
    save : bool
        A flag indicating whether or not to save the queried data to a csv. The default
        is to save the queried data. 
    outdir : str
        The directory path to save the queried data to. The default location is the current
        working directory. 

    Returns:
    ---------------
    sun_position_df : pandas.core.frame.DataFrame
        A pandas DataFrame containing the sun position for the requested date and location. 
    """
    if filename == "default":
        filename = default_filename(day, month, year)

    data = query_website(day=day, month=month, year=year, latitude=latitude, longitude=longitude, time_zone=time_zone, filename=filename)

    filename, date, lat_degrees, lon_degrees = get_title_info(data)
    df = get_alt_az(data, time_zone=time_zone)

    df["date"] = date
    df["latitude_degrees"] = lat_degrees
    df["longitude_degrees"] = lon_degrees
    df["time_zone"] = time_zone

    if save:
        df.to_csv(f"{outdir}/{filename}.csv", index=False)
        print(f"saving file to: {outdir}/{filename}.csv")

    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="queries website of the Astronomical Applications Department of the US Naval Observatory and makes a table of the sun's altitude and azimuth over the course of a day for a given location")
    parser.add_argument("day", help='date to query sun position', type=int)
    parser.add_argument("month", help='date to query sun position', type=int)
    parser.add_argument("year",help='date to query sun position', type=int)
    parser.add_argument("-latitude", "-lat", help="coordinates to pull data for. Must be given in degrees. Defaults to the location of the CHIME outrigger at Green Bank Observatory", default=38.43, type=float)
    parser.add_argument("-longitude", "-lon", help="coordinates to pull data for. Must be given in degrees. Defaults to the location of the CHIME outrigger at Green Bank Observatory", default= -79.83, type=float)
    parser.add_argument("-time_zone", "-tz", help="local time zone to set data to. Default is EDT (UTC-4)", type=int, default=-4)
    parser.add_argument("-filename", '-f', help="filename to save data under. Default is 'YYYY_DDD_CHIME.csv'", default="default")
    parser.add_argument("-outdir", '-o', help='directory to save csv to. Default is the current working directory', default=os.getcwd())
    args = parser.parse_args()


    get_sun_position(day=args.day, 
                     month=args.month, 
                     year=args.year, 
                     latitude=args.latitude, 
                     longitude=args.longitude, 
                     time_zone=args.time_zone, 
                     filename=args.filename, 
                     save=True, 
                     outdir=args.outdir)
