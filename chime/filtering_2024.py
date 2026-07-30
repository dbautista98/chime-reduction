#imports:

from chime.calibration import load_Learmonth_data
from scipy import interpolate

import numpy as np
import glob
from tqdm import trange
import os
from datetime import datetime
import pandas as pd

def filtering(df):
    '''
    This function takes in two arguments, median and result.  Median takes in the Learmonth data
    and plucks out the days that have good data.  This means days that have some form of flux and then
    calculates the median of that certian day, making sure to leave out the bad days of data.'''
    
    median = (not np.isnan(np.nanmedian(df['410']))) and np.nanmedian(df['410']) !=1 and np.nanmedian(df['410'])
    result = median
    return result

def date_values(good_dat, bad_dat):
    '''
    There are 2 arguments present in this function:
        good_dat: list of data that was made above, that holds all the good data that was filtered out of 
        the original list
        bad_dat: list of the data that filters out all the days that have only NaNs in their system.
    This function's purpose is to change these datetime values in the lists above into usable numbers 
    for interpoliation reasons'''
    
    good_date = []  #dates in numbered values, same with the bad list times
    bad_date = [] # NaN dates that do not have real values but the files exist
    
    for date in good_dat:
        base = os.path.basename(date)[3:7]
        num_date = int(base)
        good_date.append(num_date)
    
    for nodate in bad_dat:
        nobase = os.path.basename(nodate)[3:7]
        no_num_date = int(nobase)
        bad_date.append(no_num_date)
    
    return good_date, bad_date

def time_of_date(good_dat, bad_dat):
    '''
    This function also has two arguments: good_dat, and bad_dat once again.  THe purpoce of this funcion
    is to convert the previous lists into a strtime form of L%y%m%d.SRD so it reconizes that form and 
    actually gives us numbers to work with.'''
    
    good_datetime = []  #putting into a list of datetimes
    bad_datetimes_NaN = [] #list of datetimes with NaN values 
    
    for good in good_dat:
        file = os.path.basename(good)
        new_var = datetime.strptime(file, "L%y%m%d.SRD")
        good_datetime.append(new_var)
        
    for bad in bad_dat:
        fileb = os.path.basename(bad)
        bad_var = datetime.strptime(fileb, "L%y%m%d.SRD")
        bad_datetimes_NaN.append(bad_var)
        
    return good_datetime, bad_datetimes_NaN

def flux_calibration(good_dat):
    '''
    This function is taking the data in good_dat and extracting the median of each individual day that exist for a 
    solar flux value through a loop.  Then afterwards, converting them from unitless counts into units of Janskys, 
    placing them into another list known as flux_Jy.'''
    
    raw_flux = [] #extracting flux values taken from Leaermonth Observatory and listing them in a list of SFU
    
    for i in trange(len(good_dat)):
        p = good_dat[i]
        df = load_Learmonth_data(p)
        raw_flux.append(np.nanmedian(df['410']))
    
    flux_Jy = [x * 10000 for x in raw_flux]  #converting the values in SFU into units of Janskys 
    return flux_Jy

#organizing by months + seeing trends:

if __name__ == "__main__":
        
    #placing the files in here from Learmonth Observatory:

    learmonth = '/home/scratch/dbautist/CHIME_archive/learmonthData/'
    learmonth_files = glob.glob(f'{learmonth}/L24*SRD') #filtering data for the year of 2024
       
    #splitting up the months-this could be altered to fit the year or range of months needed
        
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    month_dict = {}

    for month in months:
        string = ""
        month_dict[month] = glob.glob(f'{learmonth}/L24{month}*SRD')

    day_path = month_dict['12'][0]
    df = load_Learmonth_data(day_path)
        
    #Filtering process:

    good_dat = [] #list with the string values for the good data
    bad_dat = [] #list full of bad data strings that has NaN 
    
    for month in months:  #loop where it takes the amount of days in a month and look for NaN values and filter the lists
        for i in trange(len(month_dict[month])):
            path = month_dict[month][i]
            df = load_Learmonth_data(path)
            
            if filtering(df):
                good_dat.append(path)
            else:
                bad_dat.append(path)
                
    #days in the year of 2024 that do not exist(the files do not exist from Learmonth)

    nonexistant_days = [datetime.strptime("L240223.SRD", "L%y%m%d.SRD"), 
                        datetime.strptime("L240224.SRD", "L%y%m%d.SRD"),
                        datetime.strptime("L240226.SRD", "L%y%m%d.SRD"),
                        datetime.strptime("L240227.SRD", "L%y%m%d.SRD"),
                        datetime.strptime("L240616.SRD", "L%y%m%d.SRD"),
                        ]
    nonexistant_days.sort()
    
    #appending the lists from the functions:

    good_date, bad_date = date_values(good_dat, bad_dat)
    good_datetime, bad_datetimes_NaN = time_of_date(good_dat, bad_dat)
    flux_Jy = flux_calibration(good_dat)

    #combining the lists of days of NaN values and nonexistant days 

    bad_datetimes_total = sorted(bad_datetimes_NaN + nonexistant_days)

    #all the dates combined 

    dates = sorted(good_date + bad_date)

    #Data sorting, filtering out days that exist from the year 2024: 
    
    known_jan_points = list(range(101, 132))
    known_feb_points = list(range(201, 230))
    known_mar_points = list(range(301, 332))
    known_apr_points = list(range(401, 431))
    known_may_points = list(range(501, 532))
    known_jun_points = list(range(601, 631))
    known_jul_points = list(range(701, 732))
    known_aug_points = list(range(801, 832))
    known_sept_points = list(range(901, 931))
    known_oct_points = list(range(1001, 1131))
    known_nov_points = list(range(1101, 1131))
    known_dec_points = list(range(1201, 1232))

    real1 = dates[0:31]      #Jan
    real2 = dates[31:56]
    real3 = dates[48:79]
    real4 = dates[80:110]
    real5 = dates[111:142]
    real6 = dates[143:178]
    real7 = dates[179:208]   #July
    real8 = dates[207:237]   #August
    real9 = dates[237:266]   #Sept
    real10 = dates[265:296]
    real11 = dates[295:325]
    real12 = dates[325:365]

    dont_existFeb = [item for item in known_feb_points if item not in real2]
    dont_existJu = [item for item in known_jun_points if item not in real6]

    dont_exist = sorted(dont_existFeb + dont_existJu)
    bad_dates_total = sorted(bad_date + dont_exist)


    #interpolating for the days of both NaN and nonexisting:

    f = interpolate.interp1d((good_date), (flux_Jy))

    good_thing = f(good_date)
    est_flux = f(bad_dates_total)

    for num in bad_dates_total:
        date_str = f"{int(num):04d}"
        full_date_str = f"2025{date_str}"
        
        dt_obj = datetime.strptime(full_date_str, "%Y%m%d")
        
    #Pandas dataframes:

    good_flux_data = {
        "Date": good_datetime,
        "Flux": flux_Jy,
        "Source": "Real"
    }

    bad_flux_data = {
        "Date": bad_datetimes_total,
        "Flux": est_flux,
        "Source": "Interpolated"
    }

    good = pd.DataFrame(good_flux_data)
    bad = pd.DataFrame(bad_flux_data)

    total = [good, bad]
    full_list = pd.concat(total)
    full_list_sort = full_list.sort_values(by=["Date"])

    full_list_sort["Date"] == str

    full_list_sort.to_csv("filtering_dat_2024_NEW.csv", index=False)