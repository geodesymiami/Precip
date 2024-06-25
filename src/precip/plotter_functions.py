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
import pygmt
from precip.helper_functions import *
from precip.download_functions import *
from precip.config import startDate, elninos, pathJetstream

# elninos = {'weak nina': [[2000.4164, 2001.1233], [2005.8712, 2006.2], [2007.5342, 2008.4548], [2008.874, 2009.2], [2010.4521, 2011.3671], [2011.6192, 2012.2027], [2016.6219, 2016.9562], [2017.7863, 2018.2849], [2020.6219, 2021.2849], [2021.7041, 2023.0384]], 'moderate nina': [[2007.7041, 2008.2877], [2010.5342, 2011.1233], [2011.7863, 2011.9534], [2020.789, 2021.0384]], 'strong nina': [[2007.8712, 2008.1233], [2010.7041, 2010.9534]], 'weak nino': [[2002.4521, 2003.1233], [2004.6219, 2005.1233], [2006.7041, 2007.0384], [2009.6192, 2010.2], [2015.2, 2016.2877], [2018.7863, 2019.3671], [2023.4521, 2024.0384]], 'moderate nino': [[2002.7041, 2002.9534], [2009.7863, 2010.1233], [2015.4521, 2016.2027], [2023.5342, 2024.0384]], 'strong nino': [[2015.5342, 2016.2027]], 'very strong nino': [[2015.7041, 2016.1233]]} 

# TODO to replace elninos with the following API #
# TODO eventually move to helper_functions.py
if False:
    # CHECK THIS FIRST https://psl.noaa.gov/enso/mei/
    req = requests.get('https://psl.noaa.gov/enso/mei/data/meiv2.data')
    print(req.text)

###################################################

def prompt_subplots(inps, jsonVolcano):
    gpm_dir = inps.dir
    volcano_json_dir = inps.dir + '/' + jsonVolcano

    if inps.download:
        dload_site_list_parallel(gpm_dir, generate_date_list(inps.download[0], inps.download[1]))

    if inps.check:
        check_nc4_files(gpm_dir)

    if inps.list:
        volcanoes_list(volcano_json_dir)

    # Generate the list of dates
    date_list = generate_date_list(inps.start_date, inps.end_date, inps.average)

    if inps.style:
        eruption_dates = []

        if inps.latitude and inps.longitude:
            inps.latitude, inps.longitude = adapt_coordinates(inps.latitude, inps.longitude)

            title = f'Latitude: {inps.latitude}, Longitude: {inps.longitude}'

        elif inps.name:
            eruption_dates, lalo = extract_volcanoes_info(volcano_json_dir, inps.name[0])
            inps.latitude, inps.longitude = adapt_coordinates(lalo[0], lalo[1])

            title = f'{inps.name[0]} - Latitude: {inps.latitude}, Longitude: {inps.longitude}'
        
        else:
            print('Error: Please provide valid coordinates or volcano name.')
            print('Try using --list to get a list of volcanoes.')
            sys.exit(1)

        if inps.style == 'strength':
            strength = True

        else:
            strength = False

        # Download missing data if any
        dload_site_list_parallel(gpm_dir, date_list)
        
        # Extract precipitation data
        precipitation = create_map(inps.latitude, inps.longitude, date_list, gpm_dir)

        # Average the precipitation data
        if inps.average in ['W', 'M', 'Y']:
            precipitation = weekly_monthly_yearly_precipitation(precipitation, inps.average)

        # Plot the map of precipitation data
        if inps.style == 'map':
            if inps.interpolate:
                precipitation = interpolate_map(precipitation, int(inps.interpolate[0]))

            map_precipitation(precipitation, inps.longitude, inps.latitude, date_list, inps.colorbar, inps.isolines, inps.vlim)

            plt.title(title)

            if not inps.no_show:
                plt.show()
            
            sys.exit(0)

        # Add cumulative, rolling precipitation, and Decimal dates columns
        precipitation = volcano_rain_frame(precipitation, roll_count)

        colors = color_scheme(inps.bins)

        quantile = quantile_name(inps.bins)

        ############################################### ERUPTIONS ##############################################

        # Create list of eruption dates and adapt to the averaged precipitation data
        if inps.add_event:            
            eruption_dates = list(eruption_dates) if not isinstance(eruption_dates, list) else eruption_dates

        if eruption_dates != []:
            eruption_dates = [datetime.strptime(date_string, '%Y-%m-%d').date() for date_string in eruption_dates]

            # Adapt the eruption dates to the averaged precipitation data
            eruption_dates = adapt_events(eruption_dates, date_list)

            # Create a dictionary where the keys are the eruption dates and the values are the same
            eruption_dict = {date: date for date in eruption_dates}

            # Map the 'Date' column to the eruption dates
            precipitation['Eruptions'] = precipitation['Date'].map(eruption_dict)

            # Convert to decimal year for plotting purposes
            precipitation['Eruptions'] = precipitation.Eruptions.apply(date_to_decimal_year)

        #########################################################################################################
            
        ######################################### COLORS ##############################################
        
        if inps.bins[0] > 1:
            legend_handles = [mpatches.Patch(color=colors[i], label=quantile + str(i+1)) for i in range(inps.bins[0])]

        else:
            legend_handles = []

        # Calculate 'color' based on ranks of the 'roll' column
        precipitation['color'] = ((precipitation['roll'].rank(method='first') * inps.bins[0]) / len(precipitation)).astype(int).clip(upper=inps.bins[0]-1)

        # Map the 'color' column to the `colors` list
        precipitation['color'] = precipitation['color'].map(lambda x: colors[x])

        ################################################################################################

        ##################### NAMING #####################

        if time_period == 'daily' or time_period == 'bar' or strength == True:
            ylabel = str(roll_count) + " day precipitation (mm)"

        else:
            ylabel = f" {time_period} precipitation (mm)"

        
        labels = {'title': title,
                'ylabel': ylabel,
                'y2label': 'Cumulative precipitation'}

        ##################################################

        precipitation = from_nested_to_float(precipitation)

        if inps.style == 'annual':
            annual_plotter(precipitation, color_count=inps.bins, roll_count=inps.roll, eruptions=eruption_dates)
        
            if inps.save:
                if inps.name:
                    saveName = inps.name[0]

                elif inps.latitude and inps.longitude:
                    saveName = f'{inps.latitude}_{inps.longitude}'
                    
                save_path = f'{inps.save}/{saveName}_{inps.start_date}_{inps.end_date}_{inps.style}.png'
                plt.savefig(save_path)
            
            if not inps.no_show:
                plt.show()

            sys.exit(0)

        else:

            ######################## STRENGTH ######################

            if strength:

                precipitation = precipitation.sort_values(by='roll') 

                precipitation = precipitation.reset_index(drop=True) 

            ########################################################
                
            legend_handles = bar_plotter_2(precipitation, strength, inps.log, labels, legend_handles)

            if elnino and not strength:
                legend_handles = plot_elninos(precipitation, legend_handles)
                
        if inps.add_event or eruption_dates != []:            
            legend_handles = plot_eruptions(legend_handles, eruption_dates, precipitation.sort_values(by=['roll'])['Decimal'], strength)
        
        plt.legend(handles=legend_handles, loc='upper left', fontsize='small')
        plt.tight_layout()

        if inps.save:
            if inps.name:
                saveName = inps.name[0]

            elif inps.latitude and inps.longitude:
                saveName = f'{inps.latitude}_{inps.longitude}'
                
            save_path = f'{inps.save}/{saveName}_{inps.start_date}_{inps.end_date}_{inps.style}.png'
            plt.savefig(save_path)
        
        if not inps.no_show:
            plt.show()

    sys.exit(0)


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

    for d in start_dates:
        print('Extracted eruption in date: ', d)

    # Return the list of start dates, the list of dates, and the coordinates of the volcano
    return start_dates, coordinates


def plot_eruptions(precipitation, legend_handles, strength):
    if strength:
        eruptions = precipitation[precipitation['Eruptions'].notna()].index

    else:
        eruptions = precipitation[precipitation['Eruptions'].notna()]['Eruptions']

    for x in eruptions:
        plt.axvline(x=x, color='black', linestyle='dashed', dashes=(9,6), linewidth=1)

    legend_handles += [Line2D([0], [0], color='black', linestyle='dashed', dashes= (3,2), label='Volcanic event', linewidth= 1)]

    return legend_handles


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


def create_map(latitude, longitude, date_list, folder):
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

##################### Try to use Jetstream ###############################
    
    ssh = connect_jetstream()
    # TODO to remove, for testing purposes
    ssh = None

    if ssh:
        stdin, stdout, stderr = ssh.exec_command(f"ls {pathJetstream}")

        # Wait for the command to finish executing
        stdout.channel.recv_exit_status()

        all_files = stdout.read().decode()

        # Get a list of all .nc4 files in the directory
        files = [f for f in all_files.split('\n') if f.endswith('.nc4')]

        client = ssh.open_sftp()

################ If Jetstream is not available ###########################
    else: 
        # Get a list of all .nc4 files in the data folder
        files = [folder + '/' + f for f in os.listdir(folder) if f.endswith('.nc4')]

        client = None

    # Check for duplicate files
    print("Checking for duplicate files...")
    
    if len(files) != len(set(files)):
        print("There are duplicate files in the list.")

    else:
        print("There are no duplicate files in the list.")

    dictionary = {}

    for file in files:
        result = process_file(file, date_list, lon, lat, longitude, latitude, client)

        if result is not None:
            dictionary[result[0]] = result[1]

    if client:
        client.close()
        ssh.close()

    df1 = pd.DataFrame(dictionary.items(), columns=['Date', 'Precipitation'])
    finaldf = pd.concat([finaldf, df1], ignore_index=True, sort=False)

    # finaldf.sort_index()
    # finaldf.sort_index(ascending=False)

    finaldf = finaldf.sort_values(by='Date', ascending=True)
    finaldf = finaldf.reset_index(drop=True)

    return finaldf


def bar_plotter(rainfall, colors,legend_handles , color_count=1, roll_count=1, eruptions=pd.DataFrame(), ninos=False, by_season=False, log_flag=True, time_period=None, title=None, strength=False):
    global elninos

    volc_rain = from_nested_to_float(rainfall)

    first_date = volc_rain['Decimal'].min()
    last_date = volc_rain['Decimal'].max() 

    start = int(first_date // 1)
    end = int(last_date // 1 + 1)
        
    # Applies a log scale to precipitation data if log_flag == True
    # if log_flag == True:
    #     y_min = volc_rain['roll'].min()
    #     volc_rain['roll'] = volc_rain['roll'].apply(lambda x: math.log(x - y_min + 1))

    plt.subplots(figsize=(10, 4.5))
    # plt.close()

    def plot_bar(dates, colors, plot, strength):
        dates_sort = dates.sort_values(by=['roll'])

        # TODO zero values influnce the quartile division, check with Falk if he wants this to be used in the case of a small dataset with no roll values
        if False:
            # Ignores zero values in the rain data
            dates_sort = dates[dates['roll'] != 0].sort_values(by=['roll'])

        dates_j = dates_sort['Decimal']
        daterain_j = dates_sort['roll']
        bin_size = len(dates_j) // color_count

        if strength == True:
            daterain_j.dropna(inplace=True)
            x = range(l*(bin_size), (l+1)*bin_size)
            y = np.array(daterain_j[l*(bin_size): (l+1)*bin_size])
            width = 1.1 #(max(x) - min(x)) / len(x)
        else:
            x = dates_j[l*(bin_size): (l+1)*bin_size]
            y = daterain_j[l*(bin_size): (l+1)*bin_size]
            width = 0.01

        plot.bar(x, y, color =colors[l], width = width, alpha = 1)
        # plt.close()

        return dates
    
    # Plots 90 day rain averages, colored by quantile
    for l in range(color_count):
        if by_season == True and strength == False:

            # Rain data is broken into quantiles, year by year, and plotted
            for j in range(start, end + 1):
                dates = volc_rain[volc_rain['Decimal'] // 1 == j].copy()
                dates = plot_bar(dates, colors, plt, strength)

        else:
            # plt.close()
            # Rain data is broken into quantiles, and plotted
            dates = plot_bar(volc_rain, colors, plt, strength)

    if log_flag == True:
        plt.yscale('log')
        plt.yticks([1, 10, 100, 1000])

    if time_period == 'daily' or time_period == 'bar' or strength == True:
        plt.ylabel(str(roll_count) + " day precipitation (mm)")

    else:
        plt.set_ylabel(f" {time_period} precipitation (mm)")

    plt.xlabel("Year")
    plt.title(title)

    # Plots cumulative rainfall in the same plot as the 90 day rain averages.
    legend_handles += [mpatches.Patch(color='gray', label='Cumulative precipitation')]

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
                    if elninos[j][i][0] <= last_date:
                        x1 = elninos[j][i][0]

                        if elninos[j][i][1] > last_date:
                            x2 = last_date

                        else:
                            x2 = elninos[j][i][1]

                        plt.plot([x1, x2], [ticks - .125, ticks - .125], color=colors[j][0], alpha=1.0, linewidth=6) 

    # Set plot properties
    # plot.set_yticks(ticks=[i for i in range(ticks)])

    if strength == False:
        plt.xticks(ticks=[start + (2*i) for i in range(((end - start) // 2) + 1)], labels=["'" + str(start + (2*i))[-2:] for i in range(((end - start) // 2) + 1)])
        plot2 = plt.twinx()
        plot2.bar(dates.Decimal, np.array(dates['cumsum']), color ='gray', width = 0.01, alpha = .05)
        plot2.set_ylabel("Cumulative precipitation (mm)", rotation=270, labelpad= 10)

    return legend_handles


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


def map_precipitation(precipitation_series, lo, la, date, colorbar, levels, vlim=None):
    """
    Plot a map of precipitation.

    Args:
        precipitation_series (pd.DataFrame or dict or ndarray): The precipitation data.
            If a DataFrame, it should have a column named 'Precipitation' containing the precipitation values.
            If a dict, it should have keys representing dates in the format 'YYYY-MM-DD' and values as precipitation arrays.
            If an ndarray, it should be a 2D array of precipitation values.
        lo (list): The longitude range [lo_min, lo_max].
        la (list): The latitude range [la_min, la_max].
        date (list): The list of dates for which precipitation is plotted.
        colorbar (str): The colormap for the plot.
        levels (list): The contour levels for the isolines.
        vlim (tuple, optional): The minimum and maximum values for the colorbar. Defaults to None.

    Returns:
        None
    """
    m_y = [28, 29, 30, 31, 365]
    # print(precipitation_series)

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

    region = [lo[0], lo[1], la[0], la[1]]

    # Add contour lines
    if not levels:
        plt = add_isolines(region)

    else:
        plt = add_isolines(region, levels, inline=True)

    plt.imshow(precip, vmin=vmin, vmax=vmax, extent=region, cmap=colorbar)
    plt.ylim(la[0], la[1])
    plt.xlim(lo[0], lo[1])

    # Add a color bar
    cbar = plt.colorbar()

    # TODO go back here to check the logic around averaging and cumulate precipitation

    if len(date) in m_y:
        cbar.set_label('mm/day')

    else:
        cbar.set_label(f'cumulative precipitation of {len(date)} days')


def plot_steps(inps, directory, event=None, average=None):
    """
    Plot the precipitation steps.

    Args:
        inps (list): List of input parameters.
        date_list (list): List of dates.
        directory (str): Directory path.
        average (str, optional): Type of average. Defaults to None.
    """
    
    # TODO old code to be removed 
    inps[0], inps[1] = adapt_coordinates(inps[0], inps[1])
    date_list = generate_date_list(inps[2], inps[3])
    prec = create_map(inps[0], inps[1], date_list, directory)
    if average:
        prec = weekly_monthly_yearly_precipitation(prec, average)
    bar_plot(prec, inps[0], inps[1])

    if event:
        plot_eruptions(event)


def annual_plotter(rainfall, color_count=1, roll_count=1, eruptions=pd.DataFrame(), ninos=None, by_season=False, title=None):
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

    volc_rain, colors, legend_handles = data_preload(rainfall, roll_count, color_count)
    volc_rain = from_nested_to_float(volc_rain)

    first_date = volc_rain['Decimal'].min()
    last_date = volc_rain['Decimal'].max() 

    start = int(first_date // 1)
    end = int(last_date // 1 + 1)

    fig, axes = plt.subplots(1, 2, gridspec_kw={'width_ratios': [4, 1]}, figsize=(20, 15)) # to get plot of combined data 1960-2020, take length of figsize and apply-> // 1.5)

    ax0 = axes[0]
    ax1 = axes[1]

    # Creates a dataframe for rainfall at a single volcano, with new columns 'Decimal', 'roll', and 'cumsum' for 
    # decimal date, rolling average, and cumulative sum respectively.


    # Creates a numpy array of decimal dates for eruptions between a fixed start and end date.
    if eruptions != []:
        eruptions = list(map(date_to_decimal_year, eruptions))

    dates = volc_rain.sort_values(by=['roll'])
    date_dec = np.array(dates['Decimal'])

    # Plots eruptions
    if len(eruptions) > 0:
        volc_x = [((i) % 1) for i in eruptions]
        volc_y = [(i // 1) + .5 for i in eruptions]
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
    if ninos == True and strength == False:
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
    ax0.set_title(title) 
    ax0.legend(handles=legend_handles, fontsize='small')
    ax1.set_title('Total (mm)') 
    ax1.set_yticks([start + (2*k) for k in range(((end + 1 - start) // 2))], [str(start + (2*k)) for k in range(((end + 1 - start) // 2))])

    # plt.show()

    return 


def bar_plotter_2 (precipitation, strength, log, labels, legend_handles):
    plt.subplots(figsize=(10, 5))

    if strength:
        precipitation = precipitation.sort_values(by='roll')
        precipitation = precipitation.reset_index(drop=True)

        width = 1.1
        x = range(len(precipitation))

    else: 
        width = 0.01
        x = precipitation['Decimal']

    y = precipitation['roll']

    ################ Define Axis properties ################

    plt.ylabel(labels['ylabel'])

    if log == True:
        plt.yscale('log')
        plt.yticks([0.1, 1, 10, 100, 1000])

    plt.xlabel('Year')

    plt.title(labels['title'])

    ticks = int((precipitation['roll'].max() * 1.5) // 1)

    plt.bar(x, y, color=precipitation['color'], width=width, alpha=1)
    
    if strength == False:
        start = int(precipitation['Decimal'].min() // 1)
        end = int(precipitation['Decimal'].max() // 1 + 1)

        plt.xticks(ticks=[start + (2*i) for i in range(((end - start) // 2) + 1)], labels=["'" + str(start + (2*i))[-2:] for i in range(((end - start) // 2) + 1)])
        plot2 = plt.twinx()
        plot2.bar(precipitation['Decimal'], precipitation['cumsum'], color ='gray', width = width, alpha = .05)

        plot2.set_ylabel("Cumulative precipitation (mm)", rotation=270, labelpad= 10)
        legend_handles += [mpatches.Patch(color='gray', label=labels['y2label'])]

    ######################################################
        
    return legend_handles


def plot_elninos(precipitation, legend_handles):
    global elninos

    cmap = plt.cm.bwr
    colors = {'strong nino':[cmap(253), 'Strong El Niño'], 'strong nina':[cmap(3), 'Strong La Niña']}

    end = precipitation['Decimal'].max()
    ticks = int((precipitation['cumsum'].max() * 1.5) // 1)

    for j in elninos:
        if j == 'strong nino' or j == 'strong nina':

            for i in range(len(elninos[j])):
                if elninos[j][i][0] <= end:
                    x1 = elninos[j][i][0]

                    if elninos[j][i][1] > end:
                        x2 = end

                    else:
                        x2 = elninos[j][i][1]

                    plt.plot([x1, x2], [ticks - .125, ticks - .125], color=colors[j][0], alpha=1.0, linewidth=6)

                    if colors[j][1] not in [i.get_label() for i in legend_handles]:
                        legend_handles += [mpatches.Patch(color=colors[j][0], label=colors[j][1])]

    return legend_handles