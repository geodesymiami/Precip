import numpy as np
from datetime import datetime, date
import calendar
import pandas as pd
from dateutil.relativedelta import relativedelta
import threading
import math
from matplotlib import cm
from matplotlib import patches as mpatches
import netCDF4 as nc
from netCDF4 import Dataset
import re
import tempfile
from precip.config import pathJetstream
import os
from pandas import NaT

# TODO maybe delete this function 
def data_preload(rainfall, roll_count, color_count):

    # Creates a dataframe for rainfall, with new columns 'Decimal', 'roll', and 'cumsum' for 
    # decimal date, rolling sum, and cumulative sum respectively.
    volc_rain = volcano_rain_frame(rainfall, roll_count)

    colors = color_scheme(color_count)
    quantile = quantile_name(color_count)

    if color_count > 1:
        legend_handles = [mpatches.Patch(color=colors[i], label=quantile + str(i+1)) for i in range(color_count)]

    else:
        legend_handles = []

    return volc_rain, colors, legend_handles


def date_to_decimal_year(date_str):
    """
    Converts a date string or date object to a decimal year.

    Parameters:
    date_str (str or datetime.date): The date string in the format 'YYYY-MM-DD' or a datetime.date object.

    Returns:
    float: The decimal year representation of the input date.

    Example:
    >>> date_to_decimal_year('2022-01-01')
    2022.0
    """
    if date_str is None or date_str is NaT:
        return None
    
    if type(date_str) == str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        except:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            
    else:
        date_obj = date_str

    year = date_obj.year
    day_of_year = date_obj.timetuple().tm_yday

    # Check if it's a leap year
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        days_in_year = 366.0
        
    else:
        days_in_year = 365.0

    decimal_year = year + (day_of_year - 1) / days_in_year
    decimal_year = round(decimal_year, 4)

    return decimal_year


def days_in_month(date):
    """
    Get the number of days in a given month.

    Args:
        date (str or datetime.date): The date in the format "YYYY-MM-DD" or a datetime.date object.

    Returns:
        int: The number of days in the month.

    Raises:
        ValueError: If the date is not in the correct format.

    """
    try:
        year, month, day = map(int, date.split("-"))
    except:
        year, month = date.year, date.month 
    
    num_days = calendar.monthrange(year, month)[1]

    return num_days


def generate_coordinate_array(longitude=[-179.95], latitude=[-89.95]):
    """
    Generate an array of coordinates based on the given longitude and latitude ranges.

    Args:
        longitude (list, optional): A list containing the minimum and maximum longitude values. Defaults to [-179.95].
        latitude (list, optional): A list containing the minimum and maximum latitude values. Defaults to [-89.95].

    Returns:
        tuple: A tuple containing the generated longitude and latitude arrays.

    The default list generated is used to reference the indexes of the precipitation array in the netCDF4 file.
    """
    try:
        lon = np.round(np.arange(longitude[0], longitude[1], 0.1), 2)
        lat = np.round(np.arange(latitude[0], latitude[1], 0.1), 2)

    except:
        lon = np.round(np.arange(longitude[0], 180.05, 0.1), 2)
        lat = np.round(np.arange(latitude[0], 90.05, 0.1), 2)

    return lon, lat


def adapt_coordinates(latitude, longitude):
    """
    Adjusts the latitude and longitude coordinates to ensure they fall within the valid range (GPM dataset resolution).

    Parameters:
    latitude (float or str or list): The latitude coordinate(s) to be adjusted.
    longitude (float or str or list): The longitude coordinate(s) to be adjusted.

    Returns:
    tuple: A tuple containing the adjusted latitude and longitude coordinates.

    Raises:
    ValueError: If any of the latitude or longitude values are not within the valid range.

    """
    if isinstance(longitude, float) or isinstance(longitude, str):
        longitude = [longitude, longitude]

    if isinstance(latitude, float) or isinstance(latitude, str):
        latitude = [latitude, latitude]

    for i in range(len(latitude)):
        
        la = int(float(latitude[i]) *  10) /  10.0

        if -89.95 <= la <= 89.95:

            val = 0.05 if la > 0 else -0.05
            latitude[i] = round(la + val, 2)

        else:
            raise ValueError(f'Values not in the Interval (-89.95, 89.95)')
            
    for i in range(len(longitude)):
        lo = int(float(longitude[i]) *  10) /  10.0

        if -179.95 <= lo <= 179.95:

            val = 0.05 if lo > 0 else  -0.05
            longitude[i] = round(lo + val, 2)
        else:
            raise ValueError(f'Values not in the Interval (-179.5, 179.5)')
        
    return latitude, longitude


def weekly_monthly_yearly_precipitation(dictionary, time_period=None):
    """
    Resamples the precipitation data in the given dictionary by the specified time period.

    Args:
        dictionary (dict): A dictionary containing precipitation data.
        time_period (str): The time period to resample the data by (e.g., 'W' for weekly, 'M' for monthly, 'Y' for yearly).

    Returns:
        pandas.DataFrame: The resampled precipitation data.

    Raises:
        KeyError: If the 'Precipitation' field is not found in the dictionary.
    """
    m_y = [28,29,30,31,365]

    if isinstance(dictionary, dict):
        df = pd.DataFrame.from_dict(dictionary)

    else:
        df = dictionary

    if df['Date'].dtype == str:
        df['Date'] = pd.to_datetime(df['Date'])

    df.set_index('Date', inplace=True)

    if 'Precipitation' in df:
        if time_period:
            # Resample the data by the time period and calculate the mean
            print('Averaging the precipitation data...')
            precipitation = df.resample(time_period[0]).mean()
            precipitation.reset_index(inplace=True)
            print('-------------------------------------------------------')

            return precipitation
    
        elif len(df) not in m_y:
            # Calculate the mean of the 'Precipitation' column
            print('Calculating the cumulative precipitation...')
            cumulative_precipitation = df['Precipitation'].cumsum().sum()
            print('-------------------------------------------------------')
            
            return cumulative_precipitation
        
        
    else:
        raise KeyError('Error: Precipitation field not found in the dictionary')


def generate_date_list(start, end=None, average='M'):
    """
    Generate a list of dates based on the given start and end dates.

    Args:
        start (str or date): The start date of the date range. Can be a string in the format 'YYYYMMDD' or 'YYYY-MM-DD',
                             or a date object.
        end (str or date, optional): The end date of the date range. Can be a string in the format 'YYYYMMDD' or 'YYYY-MM-DD',
                                     or a date object. If not provided, the current date will be used.
        average (str or tuple or list, optional): The average period for the date range. Can be 'M' for monthly or 'Y' for yearly.
                                                  If a tuple or list is provided, the first element will be used as the average period.
                                                  Defaults to 'M'.

    Returns:
        list: A list of dates ranging from the start date to the end date.

    Raises:
        ValueError: If the start or end date is not in a valid format.

    """

    if average:
        if isinstance(average, tuple) or isinstance(average, list):
            average = average[0]

    else:
        average = 'M'

    if isinstance(start, str):
        try:
            sdate = datetime.strptime(start,'%Y%m%d').date()

        except:
            sdate = datetime.strptime(start,'%Y-%m-%d').date()

    elif isinstance(start, date):
        try:
            sdate = start.date()

        except:
            sdate = start

    if isinstance(end, str):
        try:
            edate = datetime.strptime(end,'%Y%m%d').date()

        except:
            edate = datetime.strptime(end,'%Y-%m-%d').date()

    elif isinstance(end, date):
        try:
            edate = end.date()

        except:
            edate = end

    elif end is None:
        if average == 'M':            
            if sdate.day == 1:
                edate = datetime(sdate.year, sdate.month, days_in_month(sdate)).date()

            else:
                edate = sdate + relativedelta(days=30)

        elif average == 'Y':
            sdate = datetime.strptime(start,'%Y%m%d').date()
            edate = sdate + relativedelta(days=365)

    if edate >= datetime.today().date():
        edate = datetime.today().date() - relativedelta(days=1)

    # Create a date range with the input dates, from start_date to end_date
    date_list = pd.date_range(start=sdate, end=edate).date

    print('Generated date list ranging from', sdate, 'to', edate, 'containing', len(date_list), 'days')

    return date_list


def process_file(file, date_list, lon, lat, longitude, latitude, client):
    """
    Process a file and extract a subset of precipitation data based on given coordinates.

    Args:
        file (str): The file path of the NetCDF file to be processed.
        date_list (list): A list of dates to filter the data.
        lon (numpy.ndarray): 1D array of longitudes.
        lat (numpy.ndarray): 1D array of latitudes.
        longitude (tuple): A tuple containing the minimum and maximum longitude values for the subset.
        latitude (tuple): A tuple containing the minimum and maximum latitude values for the subset.

    Returns:
        tuple: A tuple containing the date as a string and the subset of precipitation data as a numpy array.
               Returns None if the date is not in the date_list or if the file cannot be opened.
    """

    # Extract date from file name
    d = re.search('\d{8}', file)
    date = datetime.strptime(d.group(0), "%Y%m%d").date()

    if date not in date_list:
        return None

    if client is not None:
        with tempfile.NamedTemporaryFile(suffix='.nc4', delete=True) as tmp:
            remote_file_path = pathJetstream + file
            
            # Download the file to your local system
            client.get(remote_file_path, tmp.name)

            # Open the NetCDF file
            ds = nc.Dataset(tmp.name)

    else:
        ds = nc.Dataset(file)

    data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']

    subset = data[:, np.where(lon == longitude[0])[0][0]:np.where(lon == longitude[1])[0][0]+1, np.where(lat == latitude[0])[0][0]:np.where(lat == latitude[1])[0][0]+1]
    subset = subset.astype(float)

    ds.close()

    return (str(date), subset)


def ask_user(operation):
    """
    Asks the user for input to perform a specific operation.

    Args:
        operation (str): The operation to be performed.

    Returns:
        bool: True if the user's answer is 'yes', False otherwise.
    """

    if operation == 'check':
        msg = "Do you want to run a check on files integrity?"

    print(msg, "(yes/no): ")
    answer = 'no'

    
    def check():
        nonlocal answer
        answer = input()
    t = threading.Thread(target=check)
    t.start()
    t.join(timeout=10)  # Wait for 10 seconds
    return answer.lower() == 'yes'


def vprint(msg, verbose):
    if verbose:
        print(msg)


def quantile_name(color_count):
    """
    Simple function used for labelling when plotting.

    Args: 
        color_count: Number of quantiles

    Return:
        quantile: string used in plot labelling

    """

    if color_count == 2:
        quantile = 'half '
    elif color_count == 3:
        quantile = 'tertile '
    elif color_count == 4:
        quantile = 'quartile '
    else:
        quantile = 'quantile '

    return quantile


def color_scheme(color_count):
    """
    Creates a list of colors to use when plotting.

    Args: 
        color_count: Number of quantiles

    Return:
        colors: List of colors

    """

    plasma_colormap = cm.get_cmap('viridis', 256)
    if color_count > 1:
        color_spacing = 90 // (color_count-1)
        half_count = math.ceil(color_count / 2)
        upp_half = math.floor(color_count / 2)
        yellows = [plasma_colormap(255 - i*color_spacing)[:3] for i in range(half_count)]
        greens = [plasma_colormap(135 + i*color_spacing)[:3] for i in range(upp_half)]
        greens.reverse()
        colors = yellows + greens 
    else:
        colors = [plasma_colormap(210)]

    return colors


def volcano_rain_frame(rainfall, roll_count, lon=None, lat=None, centered=False, cumsum=True):
    """ Uses lat/lon, date, and rainfall amount to create a new dataframe that includes site specific decimal dates, rolling average rain, and cumulative rain.

    Args:
        rainfall: Satellite rain dataframe for volcanos in chosen region. 
        volcanos: A dictionary of sites (eg. sites_dict = {'Wolf': (-91.35, .05, 'Wolf'), 'Fernandina': (-91.45, -.45, 'Fernandina')}).
        pick: volcano or site at which to collect data.  
        roll_count: Number of days to average rain over.

    Return:
        volc_rain: A new dataframe with additional columns for decimal date, rolling average, and cumulative rain.

    """    

    # Would be useful if we decide to average over nearby coordinates.
    # lat = volcanos[pick][1]
    # lon = volcanos[pick][0]
    # nearby_rain = rainfall[(abs(lon - rainfall['Longitude']) <= lon_range) & (abs(lat - rainfall['Latitude']) <= lat_range)].copy()
    # dates = np.sort(nearby_rain['Date'].unique())
    # averages = [[date, nearby_rain['Precipitation'][nearby_rain['Date'] == date].mean()] for date in dates]
    # volc_rain = pd.DataFrame(averages, columns = ['Date', 'Precipitation'])

    if lon == None:
        volc_rain = rainfall.copy()

    elif lon == 'NaN':
        volc_rain = rainfall[(rainfall['Longitude'].isna()) & (rainfall['Latitude'].isna())].copy()

    else:    
        volc_rain = rainfall[(rainfall['Longitude'] == lon) & (rainfall['Latitude'] == lat)].copy()

    if 'Decimal' not in rainfall.columns:
        volc_rain['Decimal'] = volc_rain.Date.apply(date_to_decimal_year)
        volc_rain = volc_rain.sort_values(by=['Decimal'])

    if 'roll' not in volc_rain.columns:
        if centered == True:
            volc_rain['roll'] = volc_rain.Precipitation.rolling(roll_count, center=True).sum()

        else:
            volc_rain['roll'] = volc_rain.Precipitation.rolling(roll_count).sum()
        
    volc_rain = volc_rain.dropna(subset=['roll'])

    if 'Precipitation' in volc_rain.columns:
        if cumsum == True:
            volc_rain['cumsum'] = volc_rain.Precipitation.cumsum()

    if 'Date' in volc_rain.columns:
        volc_rain['Date'] = pd.to_datetime(volc_rain['Date'])
        
    return volc_rain


def from_nested_to_float(dataframe):
    """ Converts a nested list of floats to a flat list of floats.

    Args:
        nested: A nested list of floats.

    Return:
        flat: A flat list of floats.

    """

    for column_name in dataframe.columns:
        try:
            dataframe[column_name] = dataframe[column_name].apply(lambda x: float(x[0][0][0]))

        except(IndexError, TypeError):
            continue

    return dataframe


def adapt_events(eruption_dates, date_list):
    # Find the closest dates in the second list for each date in the first list
    if not isinstance(eruption_dates, list):
        eruption_dates = list(eruption_dates)

    valid_eruption_dates = []

    for i in range(len(eruption_dates)):
        # TODO remember this was a test
        eruption_date = pd.Timestamp(eruption_dates[i]).normalize()

        if eruption_date < date_list.iloc[0]:
            continue

        for j in range(len(date_list)):
            try:
                if date_list.iloc[j] <= eruption_date < date_list.iloc[j+1]:
                    valid_eruption_dates.append(date_list.iloc[j])
                    break

            except:
                # Only add the date to valid_eruption_dates if it's not greater than the last date in date_list
                if eruption_date <= date_list.iloc[j]:
                    valid_eruption_dates.append(date_list.iloc[j])
                
                else:
                    print(f'Removing {eruption_dates} from the list of eruptions. Out of range')

    return valid_eruption_dates