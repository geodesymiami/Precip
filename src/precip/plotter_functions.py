from download_functions import crontab_volcano_json
import os
import json
from datetime import datetime
import sys
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as plt
from helper_functions import date_to_decimal_year
import numpy as np
from scipy.interpolate import interp2d
import re
import netCDF4 as nc
import pygmt
from precip.src.precip.helper_functions import generate_coordinate_array


def volcanoes_list(jsonfile):
    """
    Retrieves a list of volcano names from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.

    Returns:
        None
    """
    ############################## Alternative API but only with significant eruptions ##############################
    
    # r = requests.get('https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes?nameInclude=Cerro')
    # volcan_json = r.json()
    # volcanoName = []

    # for item in volcan_json['items']:
    #     if item['name'] not in volcanoName:
    #         volcanoName.append(item['name'])

    # for volcano in volcanoName:
    #     print(volcano)

    # print(os.getcwd())

    ####################################################################################################################

    if not os.path.exists(jsonfile):
        crontab_volcano_json(jsonfile)

    f = open(jsonfile)
    data = json.load(f)
    volcanoName = []

    for j in data['features']:
        if j['properties']['VolcanoName'] not in volcanoName:
            volcanoName.append(j['properties']['VolcanoName'])

    for volcano in volcanoName:
        print(volcano)


def extract_volcanoes_info(jsonfile, volcanoName):
    """
    Extracts information about a specific volcano from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.
        volcanoName (str): The name of the volcano to extract information for.

    Returns:
        tuple: A tuple containing the start dates of eruptions, a date list, and the coordinates of the volcano.
    """
    if not os.path.exists(jsonfile):
        crontab_volcano_json(jsonfile)

    f = open(jsonfile)
    data = json.load(f) 
    start_dates = []
    first_day = datetime.strptime('2000-06-01', '%Y-%m-%d').date()
    last_day = datetime.today().date() - relativedelta(days=1)

    for j in data['features']:
        if j['properties']['VolcanoName'] == volcanoName:

            name = (j['properties']['VolcanoName'])
            start = datetime.strptime((j['properties']['StartDate']), '%Y%m%d').date()
            try:
                end = datetime.strptime((j['properties']['EndDate']), '%Y%m%d').date()
            except:
                end = 'None'
            
            print(f'{name} eruption started {start} and ended {end}')

            if start >= first_day and start <= last_day:
                start_dates.append(start)
                coordinates = j['geometry']['coordinates']
                coordinates = coordinates[::-1]

    if not start_dates:
        print(f'Error: {volcanoName} eruption date is out of range')
        sys.exit(1)

    start_dates = sorted(start_dates)
    first_date = start_dates[0]

    if first_date - relativedelta(days=90) >= first_day:
        first_date = first_date - relativedelta(days=90)
    else:
        first_date = first_day

    date_list = pd.date_range(start = first_date, end = start_dates[-1]).date

    return start_dates, date_list, coordinates


def plot_eruptions(start_date):
    """
    Plot vertical lines on a graph to indicate eruption dates.

    Parameters:
    start_date (list): A list of eruption start dates.

    Returns:
    None
    """
    for date in start_date:
        plt.axvline(x = date_to_decimal_year(str(date)), color='red', linestyle='--', label='Eruption Date')


def interpolate_map(dataframe, resolution=5):
    """
    Interpolates a precipitation map using scipy.interpolate.interp2d.

    Parameters:
    dataframe (pandas.DataFrame): The input dataframe containing the precipitation data.
    resolution (int): The resolution factor for the interpolated map. Default is 5.

    Returns:
    numpy.ndarray: The interpolated precipitation map.
    """
    
    try:
        values = dataframe.get('Precipitation')[0][0]

    except:
        values = dataframe[0]

    x = np.arange(values.shape[1])
    y = np.arange(values.shape[0])
    # Create the interpolator function
    interpolator = interp2d(x, y, values)

    # Define the new x and y values with double the resolution
    new_x = np.linspace(x.min(), x.max(), values.shape[1]*resolution)
    new_y = np.linspace(y.min(), y.max(), values.shape[0]*resolution)

    # Perform the interpolation
    new_values = interpolator(new_x, new_y)

    return new_values


def process_file(file, date_list, lon, lat, longitude, latitude):
    # Extract date from file name
    d = re.search('\d{8}', file)
    date = datetime.strptime(d.group(0), "%Y%m%d").date()

    if date not in date_list:
        return None

    # Open the file
    ds = nc.Dataset(file)

    data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']

    subset = data[:, np.where(lon == longitude[0])[0][0]:np.where(lon == longitude[1])[0][0]+1, np.where(lat == latitude[0])[0][0]:np.where(lat == latitude[1])[0][0]+1]
    subset = subset.astype(float)

    ds.close()

    return (str(date), subset)


def create_map(latitude, longitude, date_list, folder): #parallel
    """
    Creates a map of precipitation data for a given latitude, longitude, and date range.

    Parameters:
    latitude (list): A list containing the minimum and maximum latitude values.
    longitude (list): A list containing the minimum and maximum longitude values.
    date_list (list): A list of dates to include in the map.
    folder (str): The path to the folder containing the data files.

    Returns:
    pandas.DataFrame: A DataFrame containing the precipitation data for the specified location and dates to be plotted.
    """
    finaldf = pd.DataFrame()
    dictionary = {}

    lon, lat = generate_coordinate_array()

    # Get a list of all .nc4 files in the data folder
    files = [folder + '/' + f for f in os.listdir(folder) if f.endswith('.nc4')]

    # Check for duplicate files
    print("Checking for duplicate files...")
    
    if len(files) != len(set(files)):
        print("There are duplicate files in the list.")
    else:
        print("There are no duplicate files in the list.")

    dictionary = {}

    for file in files:
        result = process_file(file, date_list, lon, lat, longitude, latitude)
        if result is not None:
            dictionary[result[0]] = result[1]


    df1 = pd.DataFrame(dictionary.items(), columns=['Date', 'Precipitation'])
    finaldf = pd.concat([finaldf, df1], ignore_index=True, sort=False)

    # finaldf.sort_index()
    # finaldf.sort_index(ascending=False)

    finaldf = finaldf.sort_values(by='Date', ascending=True)
    finaldf = finaldf.reset_index(drop=True)

    return finaldf


def bar_plot(precipitation, lat, lon, volcano=''):
    """
    Generate a bar plot of precipitation data.

    Parameters:
    - precipitation (dict or DataFrame): Dictionary or DataFrame containing precipitation data.
    - lat (float): Latitude value.
    - lon (float): Longitude value.
    - volcano (str, optional): Name of the volcano. Defaults to an empty string.

    Returns:
    None
    """

    if type(precipitation) == dict:
        precipitation = pd.DataFrame(precipitation.items(), columns=['Date', 'Precipitation'])

    # Convert array into single values
    precipitation['Precipitation'] = precipitation['Precipitation'].apply(lambda x: x[0][0][0])
    precipitation.sort_values(by='Date', ascending=True, inplace=True)
    
    # Convert date strings to decimal years
    #TODO to complete
    if 'Non mensile o annuale':
        precipitation['Decimal_Year'] = precipitation['Date'].apply(date_to_decimal_year)
        precipitation_field = 'Decimal_Year'
    
    else:
        precipitation_field = 'Date'

    # Calculate the cumulative precipitation
    precipitation["cum"] = precipitation.Precipitation.cumsum()

    fig, ax = plt.subplots(layout='constrained')

    plt.bar(precipitation[precipitation_field], precipitation['Precipitation'], color='maroon', width=0.00001 * len(precipitation))
    plt.ylabel("Precipitation [mm]")

    precipitation.plot(precipitation_field, 'cum', secondary_y=True, ax=ax)

    if volcano == '':
        plt.title(f'Latitude: {lat}, Longitude: {lon}')
    else:
        plt.title(f'{volcano} - Latitude: {lat}, Longitude: {lon}')

    # ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")
    ax.get_legend().remove()

    plt.xticks(rotation=90)


def add_isolines(region, levels=0, inline=False):
    grid = pygmt.datasets.load_earth_relief(resolution="01m", region=region)

    if not isinstance(levels, int):
        levels = int(levels[0])

    # Convert the DataArray to a numpy array
    grid_np = grid.values

    # Perform the operation
    grid_np[grid_np < 0] = 0

    # Convert the numpy array back to a DataArray
    grid[:] = grid_np

    # Plot the data
    cont = plt.contour(grid, levels=levels, colors='white', extent=region)

    if levels !=0:
        plt.clabel(cont, inline=inline, fontsize=8)
        print(inline)
    
    return plt


def map_precipitation(precipitation_series, lo, la, date, work_dir, colorbar, levels,vlim=None):
    '''
    Maps the precipitation data on a given region.

    Args:
        precipitation_series (pd.DataFrame or dict or ndarray): The precipitation data series.
            If a pd.DataFrame, it should have a column named 'Precipitation' containing the data.
            If a dict, it should have date strings as keys and precipitation data as values.
            If an ndarray, it should contain the precipitation data directly.
        lo (list): The longitude range of the region.
        la (list): The latitude range of the region.
        date (list): The date of the precipitation data.
        work_dir (str): The path to the shapefile for plotting the island boundary.
        vlim (tuple, optional): The minimum and maximum values for the color scale. Defaults to None.

    Returns:
        None
    '''
    m_y = [28,29,30,31,365]
    print(precipitation_series)

    if type(precipitation_series) == pd.DataFrame:
        precip = precipitation_series.get('Precipitation')[0][0]

    elif type(precipitation_series) == dict:
        precip = precipitation_series[date[0].strftime('%Y-%m-%d')]

    else:
        precip = precipitation_series

    precip = np.flip(precip.transpose(), axis=0)

    if not vlim:
        vmin = 0
        vmax = precip.max()

    else:
        vmin = vlim[0]
        vmax = vlim[1]

    region = [lo[0],lo[1],la[0],la[1]]

    # Add contour lines
    if not levels:
        plt = add_isolines(region)
    else:
        plt = add_isolines(region, levels, inline=True)

    plt.imshow(precip, vmin=vmin, vmax=vmax, extent=region,cmap=colorbar)
    plt.ylim(la[0], la[1])
    plt.xlim(lo[0], lo[1])

    # add a color bar
    cbar = plt.colorbar()

    if len(date) in m_y:
        cbar.set_label('mm/day')
    else :
        cbar.set_label(f'cumulative precipitation of {len(date)} days')
    
    plt.show()
    print('DONE')