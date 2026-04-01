import urllib.request
import pandas as pd
import argparse
import os
from datetime import datetime

def default_filename(day, month, year):
    time_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
    YYYY_DD = time_obj.strftime("%Y_%j")
    return f"{YYYY_DD}_CHIME"

def query_website(day, month, year, latitude=38.43, longitude=-79.83, time_zone=-4, filename="default"):
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

def get_alt_az(data):
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

    data_dict = {"time":times, "altitude":altitude, "azimuth":azimuth}
    df = pd.DataFrame(data_dict)

    return df

def get_sun_position(day, month, year, latitude=38.43, longitude=-79.83, time_zone=-4, filename="default", save=False, outdir="."):
    if filename == "default":
        filename = default_filename(day, month, year)
    
    data = query_website(day=day, month=month, year=year, latitude=latitude, longitude=longitude, time_zone=time_zone, filename=filename)

    filename, date, lat_degrees, lon_degrees = get_title_info(data)
    df = get_alt_az(data)

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
    