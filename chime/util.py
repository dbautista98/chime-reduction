import os
from datetime import datetime

def check_dir(filepath):
    """
    Checks the existence of a filepath, and if it does not exist, it will create it. 

    Arguments:
    ---------------
    filepath : str
        the filepath whose existence is to be confirmed
    """
    if os.path.exists(filepath):
        return
    else:
        os.mkdir(filepath)
        return

def get_date(filepath):
    """
    The naming convention of the CHIME data was determined to be YYYY_DDD (%Y_%j in 
    date abbreviation format) -- see python strftime abbreviations here: 
    https://www.bairesdev.com/tools/strftime/

    The filepath of the .npy files have the timestamps recorded in UTC, whereas
    the timestamps inside the file are converted to ET and need to be moved back to UTC.
    This function returns the day the data was taken, based on the UTC start time. 

    Arguments:
    ---------------
    filepath : str
        The CHIME file name to derive the date from. 

    Returns:
    ---------------
    YYYY_DDD : str
        The standardized format of the date of an observation. 
    """
    filename = os.path.basename(filepath)
    start_date = filename.split("_")[2]
    time_UTC  = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
    YYYY_DDD = time_UTC.strftime("%Y_%j")
    return YYYY_DDD 

def yyyy_ddd_to_Y_m_d(YYYY_DDD):
    """
    This is a useful function to convert back from the standardized form to a calendar
    date. This is useful when going back to look up some data. 

    Example: 
    yyyy_ddd_to_Y_m_d("2026_001")
    >>> '2026-01-01'

    Arguments:
    ---------------
    YYYY_DDD : str
        The standardized date to convert to. 

    Returns:
    ---------------
    calendar_date : str
        The calendar date in year-month-day format
    """
    datetime_obj = datetime.strptime(YYYY_DDD, "%Y_%j")
    standard_date = datetime_obj.strftime("%Y-%m-%d")
    return standard_date
