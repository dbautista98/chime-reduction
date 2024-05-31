from datetime import datetime
import wget
import os
import argparse

# year = 24
# month = 5
# day = 2



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="queries website for the solar flux value")
    parser.add_argument("day", help='date to query sun position', type=int)
    parser.add_argument("month", help='date to query sun position', type=int)
    parser.add_argument("year",help='date to query sun position', type=int)
    # parser.add_argument("-latitude", "-lat", help="coordinates to pull data for. Must be given in degrees. Defaults to the location of the CHIME outrigger at Green Bank Observatory", default=38.43, type=float)
    # parser.add_argument("-longitude", "-lon", help="coordinates to pull data for. Must be given in degrees. Defaults to the location of the CHIME outrigger at Green Bank Observatory", default= -79.83, type=float)
    # parser.add_argument("-time_zone", "-tz", help="local time zone to set data to. Default is EDT (UTC-4)", type=int, default=-4)
    # parser.add_argument("-filename", '-f', help="filename to save data under. Default is 'YYYY_DDD_CHIME.csv'", default="default")
    parser.add_argument("-outdir", '-o', help='directory to save csv to. Default is the current working directory', default=os.getcwd())
    parser.add_argument("-quiet", "-q", help="quiet wget outputs", action="store_true", default=False)
    args = parser.parse_args()

    if args.year > 100:
        format_str = "%Y/%m/%d"
    else:
        format_str = "%y/%m/%d"

    if args.quiet:
        quiet = "-q"
    else:
        quiet = ""

    datetime_obj = datetime.strptime(f"{args.year}/{args.month}/{args.day}", format_str)
    query_date = datetime_obj.strftime("%y%m%d")
    query_year = datetime_obj.strftime("%Y")

    query_URL = f"https://www.sws.bom.gov.au/Category/World%20Data%20Centre/Data%20Display%20and%20Download/Solar%20Radio/station/learmonth/SRD/{query_year}/L{query_date}.SRD"
    
    os.system(f"wget {quiet} -P {args.outdir} {query_URL}")
