import os
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
from scipy.interpolate import interp2d
import pygmt

# KA: Don't use import *
from precip.helper_functions import *
from precip.download_functions import *
from precip.config import JSON_DOWNLOAD_URL, START_DATE, END_DATE, ELNINOS
import requests


VOLCANO_FILE = os.environ.get('PRECIP_HOME') + '/src/precip/Holocene_Volcanoes_precip_cfg.xlsx'

# TODO to replace elninos with the following API #
# TODO eventually move to helper_functions.py
if False:
    # CHECK THIS FIRST https://psl.noaa.gov/enso/mei/
    req = requests.get('https://psl.noaa.gov/enso/mei/data/meiv2.data')
    print(req.text)

###################################################


def get_volcano_json(jsonfile, url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as err:
        print ("Error: ",err)
        print("Loading from local file")

        if not os.path.exists(jsonfile):
            download_volcano_json(jsonfile, JSON_DOWNLOAD_URL)

        f = open(jsonfile)
        data = json.load(f)

    return data


def volcanoes_list(jsonfile):
    """
    Retrieves a list of volcano names from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.

    Returns:
        None
    """
    data = get_volcano_json(jsonfile, JSON_DOWNLOAD_URL)

    volcanoName = []
    volcanoId = []

    for j in data['features']:
        if j['properties']['VolcanoName'] not in volcanoName:
            volcanoName.append(j['properties']['VolcanoName'])
            volcanoId.append(j['properties']['VolcanoNumber'])

    for volcano, id in zip(volcanoName, volcanoId):
        print(f'{volcano}, id: {id}')

    return volcanoName


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

    data = get_volcano_json(jsonfile, JSON_DOWNLOAD_URL)

    start_dates = []
    frame_data = []
    name = ''

    first_day = datetime.strptime(START_DATE, '%Y%m%d').date()
    last_day = datetime.strptime(END_DATE, '%Y%m%d').date()

    # Iterate over the features in the data
    for j in data['features']:
        if j['properties']['VolcanoName'] == volcanoName:
            id = j['properties']['VolcanoNumber']
            name = (j['properties']['VolcanoName'])
            start = datetime.strptime((j['properties']['StartDate']), '%Y%m%d').date()

            coordinates = j['geometry']['coordinates']
            coordinates = coordinates[::-1]
            try:
                end = datetime.strptime((j['properties']['EndDate']), '%Y%m%d').date()

            except:
                end = 'None'

            print(f'{name} (id: {id}) eruption started {start} and ended {end}')

            # If the start date is within the date range
            if start >= first_day and start <= last_day:
                start_dates.append(start)

            if strength:
                stren = j['properties']['ExplosivityIndexMax']
                frame_data.append([name, start, end, stren])

            break

    if name == '':
        volc_dict = get_volcanoes()
        coordinates = [volc_dict[volcanoName]['latitude'], volc_dict[volcanoName]['longitude']]
        id = volc_dict[volcanoName]['id']

    if strength:
    # If no start dates were found within the date range
        df = pd.DataFrame(frame_data, columns=column_names)
        return df

    # else:
    #     if not start_dates:
    #         # Print an error message and exit the program
    #         msg = f'Error: {volcanoName} eruption date is out of range'
    #         raise ValueError(msg)

    if start_dates != []:

        start_dates = sorted(start_dates)

        print('---------------------------------')
        print('Sorting eruptions by date...')
        print('---------------------------------')

        for d in start_dates:
            print('Extracted eruption in date: ', d)

    print('---------------------------------')
    print('')

    return start_dates, coordinates, id


def get_volcanoes():
    df = pd.read_excel(VOLCANO_FILE, skiprows=1)
    df = df[df['Precip'] != False]

    volcano_dict = {
        r['Volcano Name'] : {
            'id': r['Volcano Number'],
            'latitude': r['Latitude'],
            'longitude': r['Longitude']
        } for _, r in df.iterrows()}

    return volcano_dict

# TODO remove from here
def plot_eruptions(precipitation, legend_handles, strength = False, axs = None):
    if axs:
        x = [i % 1 for i in precipitation['Eruptions']]  # Take the decimal part of the date i.e. 0.25
        y = [(i // 1) + .5 for i in precipitation['Eruptions']]  # Take the integer part of the date i.e. 2020
        scatter_size = 219000 // len(precipitation['Date'].unique())
        eruption = axs.scatter(x, y, color='black', marker='v', s=scatter_size, label='Volcanic Events')
        legend_handles.append(eruption)

        return legend_handles

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


def map_precipitation(precipitation_series, lo, la, date, colorbar, levels, labels, vlim=None):
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
    # TODO go back here to check the logic around averaging and cumulate precipitation
    m_y = [28, 29, 30, 31, 365]

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

    cbar.set_label(labels['ylabel'])
    plt.title(labels['title'])


def bar_plotter (precipitation, strength, log, labels, legend_handles):
    # TODO better plot x axis
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

    if not strength:
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


def annual_plotter(precipitation, legend_handles, labels):
    global ELNINOS

    first_date = precipitation['Decimal'].min()
    last_date = precipitation['Decimal'].max()

    start = int(first_date // 1)
    end = int(last_date // 1 + 1)

    fig, axes = plt.subplots(1, 2, gridspec_kw={'width_ratios': [4, 1]}, figsize=(18, 13)) # to get plot of combined data 1960-2020, take length of figsize and apply-> // 1.5)

    ax0 = axes[0]
    ax1 = axes[1]

    # TODO by_season
    # Plots rain by quantile, and if by_season is True, then also by year.
    if False:
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

    x = precipitation['Decimal'] % 1
    y = precipitation['Decimal'] // 1
    ax0.scatter(x, y, color=precipitation['color'], marker='s', s=(219000 // len(precipitation['Date'].unique())))

    ################### SIDEPLOT OF CUMULATIVE PER YEAR ###################

    totals = []
    for year in range(start, end+1):
        totals.append(precipitation['Precipitation'][precipitation['Decimal'] // 1 == year].sum())

    ax1.barh(range(start, end+1), totals, height=.5, color='purple')

    ########################################################################

    # Set plot properties
    ax0.set_yticks([start + (2*k) for k in range(((end + 2 - start) // 2))], [str(start + (2*k)) for k in range(((end + 2 - start) // 2))])
    ax0.set_xticks([(1/24 + (1/12)*k) for k in range(12)], ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])
    ax0.set_xlabel("Month")
    ax0.set_ylabel("Year")
    ax0.set_title(labels['title'])
    ax1.set_title('Total (mm)')
    ax1.set_yticks([start + (2*k) for k in range(((end + 1 - start) // 2))], [str(start + (2*k)) for k in range(((end + 1 - start) // 2))])

    return legend_handles, axes[0]


def plot_elninos(precipitation, legend_handles, axs=None):
    global ELNINOS

    cmap = plt.cm.bwr
    colors = {'strong nino': [cmap(253), 'Strong El Niño'], 'strong nina': [cmap(3), 'Strong La Niña']}

    end = precipitation['Decimal'].max()
    ticks = int((precipitation['cumsum'].max() * 1.5) // 1)
    linewidth = 21900 // len(precipitation['Date'].unique())

    for j in ['strong nino', 'strong nina']:
        for x1, x2 in ELNINOS[j]:
            if x1 > end:
                continue

            x2 = min(x2, end)

            if axs:
                y1, x1 = divmod(x1, 1)  # Split 2000.25 into 2000 and 0.25
                y2, x2 = divmod(x2, 1)

                if y1 == y2:
                    axs.plot([x1, x2], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                else:
                    axs.plot([x1, 1.0022], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                    axs.plot([-.0022, x2], [y2 - .17, y2 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
            else:
                plt.plot([x1, x2], [ticks - .125, ticks - .125], color=colors[j][0], alpha=1.0, linewidth=6)

            if colors[j][1] not in [i.get_label() for i in legend_handles]:
                legend_handles.append(mpatches.Patch(color=colors[j][0], label=colors[j][1]))

    return legend_handles
