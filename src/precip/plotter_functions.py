import os
import json
from datetime import datetime
import sys
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
from scipy.interpolate import interp2d
import re
import netCDF4 as nc
import pygmt
from precip.helper_functions import *
from precip.download_functions import *
from precip.config import startDate

elninos = {'weak nina': [[2000.4164, 2001.1233], [2005.8712, 2006.2], [2007.5342, 2008.4548], [2008.874, 2009.2], [2010.4521, 2011.3671], [2011.6192, 2012.2027], [2016.6219, 2016.9562], [2017.7863, 2018.2849], [2020.6219, 2021.2849], [2021.7041, 2023.0384]], 'moderate nina': [[2007.7041, 2008.2877], [2010.5342, 2011.1233], [2011.7863, 2011.9534], [2020.789, 2021.0384]], 'strong nina': [[2007.8712, 2008.1233], [2010.7041, 2010.9534]], 'weak nino': [[2002.4521, 2003.1233], [2004.6219, 2005.1233], [2006.7041, 2007.0384], [2009.6192, 2010.2], [2015.2, 2016.2877], [2018.7863, 2019.3671], [2023.4521, 2024.0384]], 'moderate nino': [[2002.7041, 2002.9534], [2009.7863, 2010.1233], [2015.4521, 2016.2027], [2023.5342, 2024.0384]], 'strong nino': [[2015.5342, 2016.2027]], 'very strong nino': [[2015.7041, 2016.1233]]} 


def prompt_subplots(inps, jsonVolcano):
    prompt_plots = []
    gpm_dir = inps.dir
    volcano_json_dir = inps.dir + '/' + jsonVolcano

    if inps.latitude and inps.longitude:
        inps.latitude, inps.longitude = adapt_coordinates(inps.latitude, inps.longitude)

    if inps.download:
        dload_site_list_parallel(gpm_dir, generate_date_list(inps.download[0], inps.download[1]))
    
    if inps.plot_daily:
        plot_steps(inps.plot_daily, gpm_dir, inps.add_event)
        prompt_plots.append('plot_daily')

    if inps.plot_weekly:
        plot_steps(inps.plot_weekly, gpm_dir, inps.add_event,"W")
        prompt_plots.append('plot_weekly')

    if inps.plot_monthly:
        plot_steps(inps.plot_monthly, gpm_dir, inps.add_event, "M")
        prompt_plots.append('plot_monthly')

    if inps.plot_yearly:    
        plot_steps(inps.plot_yearly, gpm_dir, inps.add_event, "Y")
        prompt_plots.append('plot_yearly')

    if inps.volcano:
        eruption_dates, date_list, lola = extract_volcanoes_info(volcano_json_dir, inps.volcano[0])
        lo, la = adapt_coordinates(lola[0], lola[1])
        dload_site_list_parallel(gpm_dir, date_list)
        prec = create_map(lo, la, date_list, gpm_dir)
        bar_plot(prec, la, lo, volcano=inps.volcano[0])
        plot_eruptions(eruption_dates) 
        plt.show()
        prompt_plots.append('volcano')

    if inps.list:
        volcanoes_list(volcano_json_dir)

        prompt_plots.append('list')

    if inps.heatmap:
        la, lo = adapt_coordinates(inps.latitude, inps.longitude)
        date_list = generate_date_list(inps.heatmap[0], inps.heatmap[1], inps.average)
       
        dataset = create_map(la, lo, date_list, gpm_dir)

        # Readapt date_list if dataset is does not cover the whole period
        date_list = generate_date_list(dataset['Date'].iloc[0], dataset['Date'].iloc[-1], inps.average)
        dataset = weekly_monthly_yearly_precipitation(dataset, inps.average)

        if inps.interpolate:
            dataset = interpolate_map(dataset, int(inps.interpolate[0]))

        map_precipitation(dataset, lo, la, date_list, './ne_10m_land', inps.colorbar, inps.isolines ,inps.vlim)

    if inps.check:
        check_nc4_files(gpm_dir)

    ##################### TODO to change #####################
    if inps.annual_plotter:
        eruption_dates, _, lola = extract_volcanoes_info(volcano_json_dir, inps.annual_plotter[0])
        lo, la = adapt_coordinates(lola[0], lola[1])
        date_list = generate_date_list(inps.annual_plotter[3], inps.annual_plotter[4])
        dload_site_list_parallel(gpm_dir, date_list)
        precipitation = create_map(lo, la, date_list, gpm_dir)
        annual_plotter(precipitation, color_count=inps.annual_plotter[1], roll_count=inps.annual_plotter[2], eruptions=eruption_dates)
        prompt_plots.append('annual')

    if inps.bar_plotter:
        eruption_dates, _, lola = extract_volcanoes_info(volcano_json_dir, inps.bar_plotter[0])
        lo, la = adapt_coordinates(lola[0], lola[1])
        date_list = generate_date_list(inps.bar_plotter[3], inps.bar_plotter[4])
        dload_site_list_parallel(gpm_dir, date_list)
        precipitation = create_map(lo, la, date_list, gpm_dir)
        bar_plotter(precipitation, color_count=inps.bar_plotter[1], roll_count=inps.bar_plotter[2], eruptions=eruption_dates)
        prompt_plots.append('bar')

    if inps.strength:
        eruption_dates, _, lola = extract_volcanoes_info(volcano_json_dir, inps.strength[0])
        lo, la = adapt_coordinates(lola[0], lola[1])
        date_list = generate_date_list(inps.strength[3], inps.strength[4])
        dload_site_list_parallel(gpm_dir, date_list)
        precipitation = create_map(lo, la, date_list, gpm_dir)
        strength(precipitation, color_count=inps.strength[1], roll_count=inps.strength[2], eruptions=eruption_dates)
        prompt_plots.append('strength')

    ##################### END to change ##################### 

    # TODO to remove or change
    plt.show()
    # return plt


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


def extract_volcanoes_info(jsonfile, volcanoName, strength=False):
    """
    Extracts information about a specific volcano from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.
        volcanoName (str): The name of the volcano to extract information for.

    Returns:
        tuple: A tuple containing the start dates of eruptions, a date list, and the coordinates of the volcano.
    """
    column_names = ['Volcano', 'Start', 'End', 'Max Explosivity']

    # Check if the JSON file exists
    if not os.path.exists(jsonfile):
        # If not, create it
        crontab_volcano_json(jsonfile)

    # Open the JSON file and load the data
    f = open(jsonfile)
    data = json.load(f) 

    # Initialize an empty list to store the eruption start dates
    start_dates = []
    frame_data = []

    # Define the start and end of the date range
    # TODO to change to be more dynamic, reflects the first date available in the gpm dataset
    first_day = datetime.strptime(startDate, '%Y%m%d').date()
    last_day = datetime.today().date() - relativedelta(days=1)

    # Iterate over the features in the data
    for j in data['features']:
        if j['properties']['VolcanoName'] == volcanoName:
            name = (j['properties']['VolcanoName'])
            start = datetime.strptime((j['properties']['StartDate']), '%Y%m%d').date()

            try:
                end = datetime.strptime((j['properties']['EndDate']), '%Y%m%d').date()

            except:
                end = 'None'
            
            print(f'{name} eruption started {start} and ended {end}')

            # If the start date is within the date range
            if start >= first_day and start <= last_day:
                start_dates.append(start)
                
                coordinates = j['geometry']['coordinates']
                coordinates = coordinates[::-1]
            
            if strength:
                stren = j['properties']['ExplosivityIndexMax']
                frame_data.append([name, start, end, stren])

    if strength:
    # If no start dates were found within the date range
        df = pd.DataFrame(frame_data, columns=column_names)
        return df

    else:
        if not start_dates:
            # Print an error message and exit the program
            print(f'Error: {volcanoName} eruption date is out of range')
            sys.exit(1)

    start_dates = sorted(start_dates)
    first_date = start_dates[0]

    if first_date - relativedelta(days=90) >= first_day:
        # Set the first date to 90 days before the first start date
        first_date = first_date - relativedelta(days=90)
    else:
        first_date = first_day

    # Create a list of dates from the first date to the last start date
    date_list = pd.date_range(start = first_date, end = start_dates[-1]).date

    # Return the list of start dates, the list of dates, and the coordinates of the volcano
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

    plt.bar(precipitation[precipitation_field], precipitation['Precipitation'], color='maroon', width=0.00001 * len(precipitation), label='Precipitation')
    plt.ylabel("Precipitation [mm]")

    precipitation.plot(precipitation_field, 'cum', secondary_y=True, ax=ax)

    if volcano == '':
        plt.title(f'Latitude: {lat}, Longitude: {lon}')

    else:
        plt.title(f'{volcano} - Latitude: {lat}, Longitude: {lon}')

    # ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")
    # ax.get_legend().remove()

    plt.xticks(rotation=90)


def bar_plotter(rainfall, color_count=1, roll_count=1, eruptions=pd.DataFrame(), ninos=None, by_season=False, log_flag=True, centered=False, cumsum=True):
    """ Plots rolling rain temporally-- y-axis is rolling rain values, and x-axis is time.

    Args:
        rainfall: Pandas dataframe with columns Date and Precipitation.
        color_count: Number of quantiles to break rain data into.
        roll_count: Number of days to average rain over.
        eruptions: Pandas dataframe with columns Volcano, Start, End, Max Explosivity.
        ninos: True if you want to include El Nino data
        by_season: True if quantiles should be made for every year separately.
        log_flag: True to use a log scale for the rain data.
        centered: True to use a centered rolling sum
        cumsum: True to plot the cumulative rainfall in gray behind the front plot.

    Return:

    """

    global elninos

    volc_rain, erupt_dates, colors, quantile, legend_handles, start, end = data_preload(rainfall, roll_count, eruptions, color_count)
    volc_rain = from_nested_to_float(volc_rain)
        
    # Applies a log scale to precipitation data if log_flag == True
    if log_flag == True:
        y_min = volc_rain['roll'].min()
        volc_rain['roll'] = volc_rain['roll'].apply(lambda x: math.log(x - y_min + 1))

    fig, plot = plt.subplots(figsize=(10, 4.5))

    # Plots 90 day rain averages, colored by quantile
    for l in range(color_count):
        if by_season == True:
            # Rain data is broken into quantiles, year by year, and plotted
            for j in range(start, end + 1):
                rain_by_year = volc_rain[volc_rain['Decimal'] // 1 == j].copy()
                rain_j = rain_by_year.sort_values(by=['roll'])
                dates_j = np.array([rain_j['Decimal']])
                daterain_j = np.array([rain_j['roll']])
                bin_size = len(dates_j) // color_count
                plot.bar(dates_j[l*(bin_size): (l+1)*bin_size], daterain_j[l*(bin_size): (l+1)*bin_size], color =colors[l], width = 0.01, alpha = 1)
        else:
            # Rain data is broken into quantiles, and plotted
            dates = volc_rain.sort_values(by=['roll'])
            date_dec = np.array(dates['Decimal'])
            date_rain = np.array(dates['roll'])
            bin_size = len(dates) // color_count
            plot.bar(date_dec[l*(bin_size): (l+1)*bin_size], date_rain[l*(bin_size): (l+1)*bin_size], color =colors[l], width = 0.01, alpha = 1)

    # Plots cumulative rainfall in the same plot as the 90 day rain averages.
    if cumsum == True:
        legend_handles += [mpatches.Patch(color='gray', label='Cumulative precipitation')]
        plot2 = plot.twinx()
        plot2.bar(dates.Decimal, np.array(dates['cumsum']), color ='gray', width = 0.01, alpha = .05)

    # Plots eruptions   
    if len(erupt_dates) > 0:
        for line_x in erupt_dates:
            plot.axvline(x=line_x, color='black', linestyle= 'dashed', dashes= (9,6), linewidth = 1)
        legend_handles += [Line2D([0], [0], color='black', linestyle='dashed', dashes= (3,2), label='Volcanic event', linewidth= 1)]

    # Used in Nino plotting to make y range similar to max bar height 
    y_max = np.max(volc_rain['roll'].max())
    ticks = int(((y_max * 1.5) // 1))

    # Plots nino/nina events
    if ninos == True:
        cmap = plt.cm.bwr
        colors = {'strong nino':[cmap(253), 'Strong El Niño'], 'strong nina':[cmap(3), 'Strong La Niña']}
        for j in elninos:
            if j == 'strong nino' or j == 'strong nina':
                legend_handles += [mpatches.Patch(color=colors[j][0], label=colors[j][1])]
                for i in range(len(elninos[j])):
                    x1 = elninos[j][i][0]
                    x2 = elninos[j][i][1]
                    plot.plot([x1, x2], [ticks - .125, ticks - .125], color=colors[j][0], alpha=1.0, linewidth=6) 

    # Set plot properties
    plot.set_ylabel(str(roll_count) + " day precipitation (mm)")
    plot.set_xlabel("Year")
    plot.set_title('tbd')
    plot.set_yticks(ticks=[i for i in range(ticks)])
    plot.set_xticks(ticks=[start + (2*i) for i in range(((end - start) // 2) + 1)], labels=["'" + str(start + (2*i))[-2:] for i in range(((end - start) // 2) + 1)])
    plot2.set_ylabel("Cumulative precipitation (mm)", rotation=270, labelpad= 10)
    plt.legend(handles=legend_handles, loc='upper left', fontsize='small')
    plt.tight_layout()

    plt.show()

    return


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
    cont = plt.contour(grid, levels=levels, colors='white', extent=region, linewidths=0.5)

    if levels !=0:
        plt.clabel(cont, inline=inline, fontsize=8)
    
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


def plot_steps(inps, directory, event=None, average=None):
    """
    Plot the precipitation steps.

    Args:
        inps (list): List of input parameters.
        date_list (list): List of dates.
        directory (str): Directory path.
        average (str, optional): Type of average. Defaults to None.
    """
    
    inps[0], inps[1] = adapt_coordinates(inps[0], inps[1])
    date_list = generate_date_list(inps[2], inps[3])
    prec = create_map(inps[0], inps[1], date_list, directory)
    if average:
        prec = weekly_monthly_yearly_precipitation(prec, average)
    bar_plot(prec, inps[0], inps[1])

    if event:
        plot_eruptions(event)


def annual_plotter(rainfall, color_count=1, roll_count=1, eruptions=pd.DataFrame(), ninos=None, by_season=False):
    """ Plots rain in horizontal bars: y-axis is year, and x-axis is month.

    Args:
        rainfall: Pandas dataframe with columns Date and Precipitation.
        color_count: Number of quantiles to break rain data into.
        roll_count: Number of days to average rain over.
        eruptions: Pandas dataframe with columns Volcano, Start, End, Max Explosivity.
        ninos: T if you want to include El Nino data
        by_season: T if quantiles should be made for every year separately.

    Return:
    """
    global elninos

    volc_rain, erupt_dates, colors, quantile, legend_handles, start, end = data_preload(rainfall, roll_count, eruptions, color_count)

    fig, axes = plt.subplots(1, 2, gridspec_kw={'width_ratios': [4, 1]}, figsize=(10, ((len(rainfall['Date'].unique())//1200)))) # to get plot of combined data 1960-2020, take length of figsize and apply-> // 1.5)

    ax0 = axes[0]
    ax1 = axes[1]

    # Creates a dataframe for rainfall at a single volcano, with new columns 'Decimal', 'roll', and 'cumsum' for 
    # decimal date, rolling average, and cumulative sum respectively.

    volc_rain = from_nested_to_float(volc_rain)

    # Creates a numpy array of decimal dates for eruptions between a fixed start and end date.
    if eruptions != []:
        erupt_dates = list(map(date_to_decimal_year, eruptions))

    dates = volc_rain.sort_values(by=['roll'])
    date_dec = np.array(dates['Decimal'])

    # Plots eruptions
    if len(erupt_dates) > 0:
        volc_x = [((i) % 1) for i in erupt_dates]
        volc_y = [(i // 1) + .5 for i in erupt_dates]
        ax0.scatter(volc_x, volc_y, color='black', marker='v', s=(219000 // (len(rainfall['Date'].unique()))), label='Volcanic Events')
        eruption = ax0.scatter(volc_x, volc_y, color='black', marker='v', s=(219000 // (len(rainfall['Date'].unique()))), label='Volcanic Events')
        legend_handles += [eruption]

    # Plots rain by quantile, and if by_season is True, then also by year.
    for i in range(color_count):
        if by_season == True:
            for j in range(start, end + 1):
                rain_by_year = volc_rain[volc_rain['Decimal'] // 1 == j].copy()
                rain_j = rain_by_year.sort_values(by=['roll'])
                dates_j = np.array([rain_j['Decimal']])
                bin_size = len(dates_j) // color_count
                x = dates_j % 1
                y = dates_j // 1
                ax0.scatter(x[i*bin_size:(i+1)*bin_size], y[i*bin_size:(i+1)*bin_size], color=colors[i], marker='s', s=(219000 // len(rainfall['Date'].unique())))
        else:
            dates = volc_rain.sort_values(by=['roll'])
            date_dec = np.array(dates['Decimal'])
            bin_size = len(dates) // color_count
            x = date_dec % 1
            y = date_dec // 1
            ax0.scatter(x[i*bin_size:(i+1)*bin_size], y[i*bin_size:(i+1)*bin_size], color=colors[i], marker='s', s=(219000 // len(rainfall['Date'].unique())))

     # Plots nino/nina events
    if ninos == True:
        colors = {'strong nino':['gray', 'Strong El Niño'], 'very strong nino':['black', 'Very strong Niño']}
        for j in elninos:
            if j == 'strong nino' or j == 'very strong nino':
                legend_handles += [mpatches.Patch(color=colors[j][0], label=colors[j][1])]
                for i in range(len(elninos[j])):
                    x1 = elninos[j][i][0] % 1
                    y1 = elninos[j][i][0] // 1
                    x2 = elninos[j][i][1] % 1
                    y2 = (elninos[j][i][1] // 1)
                    if y1 == y2:
                        ax0.plot([x1, x2], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=(21900 // len(rainfall['Date'].unique())))
                    else:
                        ax0.plot([x1, 1.0022], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=(21900 // len(rainfall['Date'].unique())))
                        ax0.plot([-.0022, x2], [y2 - .17, y2 - .17], color=colors[j][0], alpha=1.0, linewidth=(21900 // len(rainfall['Date'].unique())))

    # Creates a sideplot that shows total rainfall by year
    totals = []
    years = [i for i in range(start, end+1)]
    for i in years:
        totals.append(volc_rain['Precipitation'][volc_rain['Decimal'] // 1 == i].sum())
    ax1.barh(years, totals, height=.5, color='purple')

    # Set plot properties
    ax0.set_yticks([start + (2*k) for k in range(((end + 2 - start) // 2))], [str(start + (2*k)) for k in range(((end + 2 - start) // 2))])
    ax0.set_xticks([(1/24 + (1/12)*k) for k in range(12)], ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])
    ax0.set_xlabel("Month") 
    ax0.set_ylabel("Year") 
    ax0.set_title('Tbd') 
    ax0.legend(handles=legend_handles, fontsize='small')
    ax1.set_title('Total (mm)') 
    ax1.set_yticks([start + (2*k) for k in range(((end + 1 - start) // 2))], [str(start + (2*k)) for k in range(((end + 1 - start) // 2))])

    plt.show()

    return 


def strength(rainfall, color_count=1, roll_count=1, eruptions=pd.DataFrame(), volcano=None, log=True):
    """ Plots the sorted rolling rain values and adds color based on quantile breakdown. Further, it plots the eruption data on top of this plot.

    Args:
        rainfall (DataFrame): Pandas dataframe with columns Date and Precipitation.
        color_count (int): Number of quantiles to break rain data into.
        roll_count (int): Number of days to average rain over.
        eruptions (DataFrame): Pandas dataframe with columns Volcano, Start, End, Max Explosivity.
        volcano (None): Not used in the function.
        log (bool): True if you want a log scale for the rain values.

    Return:
        None
    """

    volc_rain, erupt_dates, colors, quantile, legend_handles, start, end = data_preload(rainfall, roll_count, eruptions, color_count)
    volc_rain = from_nested_to_float(volc_rain)

    # Order rain data by 'roll' amount
    dates = volc_rain.sort_values(by=['roll']).copy()
    dates.dropna()
    date_dec = np.array(dates['Decimal'])
    date_rain = np.array(dates['roll'])

    plt.figure(figsize=(10, 5))

    # Plots the ordered rain data
    if color_count > 1:
        bin_size = len(dates) // color_count

        for l in range(color_count):
            y = date_rain[l*(bin_size): (l+1)*bin_size]
            plt.bar(range(l*(bin_size), (l+1)*bin_size), y, color=colors[l], width=1.1)

    else:
        plt.bar(range(len(date_rain)), date_rain, color=colors[0], width=1)  

    # Plots the eruptions as dotted vertical lines
    if not eruptions == []:
        legend_handles += [Line2D([0], [0], color='black', linestyle='dashed', dashes= (3,2), label='Volcanic event', linewidth= 1)] 

        for i in range(len(date_dec)):
            if date_dec[i] in erupt_dates:
                line_color = 'black'
                plt.axvline(x=i, color=line_color, linestyle= 'dashed', dashes= (9,6), linewidth = 1)

    # Set plot properties
    plt.title('tbd')
    plt.xlabel('Days sorted by ' + str(roll_count) + ' day precipitation')
    plt.ylabel('Rainfall (mm)')
    if log == True:
        plt.yscale('log')
        plt.yticks([1, 10, 100, 1000])
    plt.legend(handles=legend_handles, fontsize='small')

    plt.show()

    return 