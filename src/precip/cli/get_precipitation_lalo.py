#!/usr/bin/env python3

import sys
import os
from datetime import datetime
import argparse
from dateutil.relativedelta import relativedelta
import sys
from precip.plotter_functions import prompt_subplots
from precip.config import *

EXAMPLE = f"""
Date format: YYYYMMDD

Example:

  Create a bar plot with a rolling average of 30 days, 3 bins (colors divided by ascending values), on a log scale for the precipitation data of Merapi volcano (if eruptions are included in the date range, they will be plotted), default start date is {startDate} and default end date is {endDate}:
    get_precipitation_lalo.py Merapi --style bar --roll 30 --bins 3 --log

  Create a bar plot ordered by strength for the precipitation data of a specific location at a given date range and save (If path not specified, the data will be downloaded either in $WORKDIR or $HOME directory + /precip_products):
    get_precipitation_lalo.py --style strength --lalo 19.5:-156.5 ---period 20190101:20210929 --save

  Create a 'Line' plot for the precipitation data of a specific location at a given date range ordered by year, with a rolling average of 10 days and 2 binsand add 2 events to the time series:
    get_precipitation_lalo.py --style annual --start-date 20190101 --end-date 20210929 --latitude 19.5 --longitude -156.5 --roll 10 --bins 2 --add-event 20200929 20210929

  Add single events and el niño/niña events to the time series:
    get_precipitation_lalo.py --style strength --lalo 19.5:-156.5 ---period 20190101:20210929 --add-event 20200929 20210929 --ninos

  Create a map plot for the precipitation data of a specific location at a given date range:
    get_precipitation_lalo.py --style map --end-date 20210929 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'

  Add limit to the scale of the colorbar and colorbar style:
    get_precipitation_lalo.py --style map --end-date 20210929 --lalo 19.5:20.5,-155.5:-156.5 --vlim -3 3 --colorbar 'RdBu'

  Download the precipitation data:
    get_precipitation_lalo.py --download

    get_precipitation_lalo.py --download 20190101 20210929 --dir '/home/user/Downloads'
  
  List all the volcanoes:
    get_precipitation_lalo.py --list

  Check if the files are corrupted:
    get_precipitation_lalo.py --check

"""

path_data = '/Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)
    
    parser.add_argument('positional', 
                        nargs='*',
                        help='Volcano name or coordinates')
    parser.add_argument('--download', 
                        action='store_true',
                        help='Use ssh')
    parser.add_argument('--start-date',
                        nargs=1,
                        metavar='YYYYMMDD', 
                        help='Start date of the search')
    parser.add_argument('--end-date',
                        nargs=1, 
                        metavar='YYYYMMDD', 
                        help='End date of the search')
    parser.add_argument('--period',
                        metavar='YYYYMMDD:YYYYMMDD, YYYYMMDD,YYYYMMDD',
                        help='Period of the search')
    parser.add_argument('--latitude', 
                        nargs='+',  
                        metavar=('MIN', 'MAX'),
                        help='Latitude')
    parser.add_argument('--longitude', 
                        nargs='+', 
                        metavar=('MIN', 'MAX'), 
                        help='Longitude')
    parser.add_argument('--lalo',
                        nargs=1,
                        metavar=('LATITUDE:LONGITUDE, LATITUDE,LONGITUDE'),
                        help='Latitude and longitude')
    parser.add_argument('--list', 
                        action='store_true', 
                        help='List volcanoes')
    parser.add_argument('--add-event',
                        nargs='*',
                        metavar=('YYYYMMDD, YYYY-MM-DD'),
                        help='Add event to the time series')
    parser.add_argument('--dir', 
                        nargs=1, 
                        metavar=('PATH'), 
                        help='Specify path to download the data, if not specified, the data will be downloaded either in $WORKDIR or $HOME directory')
    parser.add_argument("--vlim", 
                        nargs=2, 
                        metavar=("VMIN", "VMAX"), 
                        default=None,
                        type=float, 
                        help="Velocity limit for the colorbar (default: None)")
    parser.add_argument('--polygon', 
                        metavar='POLYGON', 
                        help='Poligon of the wanted area (Format from ASF Vertex Tool https://search.asf.alaska.edu/#/)')
    parser.add_argument('--interpolate',
                        nargs=1,
                        metavar=('GRANULARITY'),
                        type=int, 
                        help='Interpolate data')
    parser.add_argument('--isolines',
                        nargs=1,
                        metavar=('LEVELS'),
                        help='Number of isolines to be plotted on the map')
    parser.add_argument('--average', 
                        choices=['D','W','M','Y'], 
                        metavar=('TIME_PERIOD'), 
                        help='Average data, default is daily')
    parser.add_argument('--check', 
                        action='store_true', 
                        help='Check if the file is corrupted')
    parser.add_argument('--colorbar', 
                        nargs=1,
                        metavar=('COLORBAR'), 
                        help='Colorbar')
    parser.add_argument('--log', 
                        action='store_true',
                        help='Enable logaritmic scale')
    parser.add_argument('--bins',
                        nargs=1,
                        type=int,
                        metavar=('BINS'),
                        help='Number of bins for the histogram')
    parser.add_argument('--roll',
                        nargs=1,
                        type=int,
                        metavar=('ROLL'),
                        help='Rolling average')
    parser.add_argument('--ninos',
                        action='store_true',
                        help='Plot Nino/Nina events')
    parser.add_argument('--name',
                        nargs=1,
                        type=str,
                        metavar=('NAME'),
                        help='Name of the volcano')
    parser.add_argument('--style',
                        choices=['daily','weekly','monthly','yearly','map','bar','annual','strength'],
                        help='Choose plot type')
    parser.add_argument('--save',
                        nargs='*',
                        metavar=('FOLDERNAME'),
                        help='Save the plot')
    parser.add_argument('--no-show',
                        action='store_true',
                        help='Do not show the plot')
    parser.add_argument('--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')
    # TODO later
    parser.add_argument('--setup',
                    help='Setup environment')

    inps = parser.parse_args()

    if not inps.dir:
        inps.dir = (os.getenv(workDir)) if workDir in os.environ else (os.getenv('HOME'))
        os.environ[workDir] = inps.dir
        inps.dir = inps.dir + '/gpm_data'

    else:
        inps.dir = inps.dir[0]

    if inps.save is not None:
        if len(inps.save) == 0:
            if prodDir in os.environ:
                inps.save = (os.getenv(prodDir))

            elif scratchDir in os.environ:
                if os.path.exists(os.getenv(scratchDir) + '/precip_products'):
                    inps.save = (os.getenv(scratchDir) + '/precip_products')

                else:
                    dir_path = os.path.join(os.getenv(scratchDir), 'precip_products')
                    os.mkdir(dir_path)
                    inps.save = dir_path

            else:
                if os.path.exists(os.getenv('HOME') + '/precip_products'):
                    inps.save = (os.getenv('HOME') + '/precip_products')

                else:
                    dir_path = os.path.join(os.getenv('HOME'), 'precip_products')
                    os.mkdir(dir_path)
                    inps.save = dir_path


        elif len(inps.save) == 1:
            inps.save = inps.save[0] 

    ############################ POSITIONAL ARGUMENTS ############################
            
    if len(inps.positional) == 1:

        # Unfortunately this can never work if we pass the coordinates since negative numbers are viewed as options
        if any(char.isdigit() for char in inps.positional):
            if 'POLYGON' in inps.positional:
                inps.latitude, inps.longitude = parse_polygon(inps.positional[0])

            else:
                coordinates = parse_coordinates(inps.positional[0])
                inps.latitude = parse_coordinates(coordinates[0])
                inps.longitude = parse_coordinates(coordinates[1])

        else:
            inps.name = inps.positional
    # Same issue here
    if len(inps.positional) == 2:
        inps.latitude = parse_coordinates(inps.positional[0])

        inps.longitude = parse_coordinates(inps.positional[1])

    ###############################################################################
                
    if not inps.period:
        inps.start_date = datetime.strptime(inps.start_date[0], '%Y%m%d').date() if inps.start_date else datetime.strptime(startDate, '%Y%m%d').date()
        #End date subject to variations, check for alternatives on config.py
        inps.end_date = datetime.strptime(inps.end_date[0], '%Y%m%d').date() if inps.end_date else datetime.strptime(endDate, '%Y%m%d').date()

    else:
        if ':' in inps.period:
            dates = inps.period.split(':')
        # TODO not sure if this is to be removed
        elif ',' in inps.period:
            dates = inps.period.split(',')

        elif ' ' in inps.period:
            dates = inps.period.split(' ')

        inps.start_date = datetime.strptime(dates[0], '%Y%m%d').date()
        inps.end_date = datetime.strptime(dates[1], '%Y%m%d').date()

    if not inps.polygon:
        
        if inps.latitude:
            if len(inps.latitude) == 1:
                inps.latitude = parse_coordinates(inps.latitude[0])

            elif len(inps.latitude) == 2:
                inps.latitude = [float(inps.latitude[0]), float(inps.latitude[1])]

            else:
                parser.error("--latitude requires 1 or 2 arguments")

        if inps.longitude:
            if len(inps.longitude) == 1:
                inps.longitude = parse_coordinates(inps.longitude[0])

            elif len(inps.longitude) == 2:
                inps.longitude = [float(inps.longitude[0]), float(inps.longitude[1])]

            else:
                parser.error("--longitude requires 1 or 2 arguments")

        if inps.lalo:
            coordinates = parse_coordinates(inps.lalo[0])
            inps.latitude = parse_coordinates(coordinates[0])
            inps.longitude = parse_coordinates(coordinates[1])

    else:
            inps.latitude, inps.longitude = parse_polygon(inps.polygon)

    if inps.style == 'weekly':
        inps.average = 'W'

    elif inps.style == 'monthly':
        inps.average = 'M'

    elif inps.style == 'yearly':
        inps.average = 'Y'

    elif inps.style == 'annual':
        inps.average = 'D'

    elif inps.style == 'map':
        if inps.average:
            inps.end_date = None

        inps.add_event = None
            
    else:
        inps.average = 'D'
    
    if inps.add_event:
        try:
            inps.add_event = tuple(datetime.strptime(date_string, '%Y-%m-%d').date() for date_string in inps.add_event)

        except ValueError:
            try:
                inps.add_event = tuple(datetime.strptime(date_string, '%Y%m%d').date() for date_string in inps.add_event)

            except ValueError:
                print('Error: Date format not valid, it must be in the format YYYYMMDD or YYYY-MM-DD')
                sys.exit(1)


    if not inps.bins:
        inps.bins = 1

    else:
        if inps.bins[0] > 4:
            inps.bins[0] = 4

        inps.bins = inps.bins[0]

    if not inps.roll:
        inps.roll = 1

    else:
        inps.roll = inps.roll[0]

    if not inps.ninos:
        inps.ninos = False

    # TODO check if is better to use true as default value
    if not inps.log:
        inps.log = False

    if not inps.colorbar:
        inps.colorbar = 'viridis'

    if inps.interpolate:
        inps.interpolate = inps.interpolate[0]

    return inps


def parse_polygon(polygon):
    """
    Parses a polygon string retreive from ASF vertex tool and extracts the latitude and longitude coordinates.

    Args:
        polygon (str): The polygon string in the format "POLYGON((lon1 lat1, lon2 lat2, ...))".

    Returns:
        tuple: A tuple containing the latitude and longitude coordinates as lists.
               The latitude list contains the minimum and maximum latitude values.
               The longitude list contains the minimum and maximum longitude values.
    """
    latitude = []
    longitude = []
    pol = polygon.replace("POLYGON((", "").replace("))", "")

    # Split the string into a list of coordinates
    for word in pol.split(','):
        if (float(word.split(' ')[1])) not in latitude:
            latitude.append(float(word.split(' ')[1]))
        if (float(word.split(' ')[0])) not in longitude:
            longitude.append(float(word.split(' ')[0]))

    longitude = [round(min(longitude),2), round(max(longitude),2)]
    latitude = [round(min(latitude),2), round(max(latitude),2)]

    return latitude, longitude


def parse_coordinates(coordinates):
    """
    Parse the given coordinates string and convert it into a list of floats.

    Args:
        coordinates (str): The coordinates string to be parsed.

    Returns:
        list: A list of floats representing the parsed coordinates.

    Raises:
        ValueError: If the coordinates string is invalid.

    """
    if isinstance(coordinates, str):
        coordinates = coordinates.replace("'", '').replace('"', '')
        
        try:
            if ',' in coordinates:
                coordinates = coordinates.split(',')

            elif ':' in coordinates:
                coordinates = coordinates.split(':')
                coordinates = [float(i) for i in coordinates]

            elif ' ' in coordinates:
                coordinates = coordinates.split(' ')
                coordinates = [float(i) for i in coordinates]

            else:
                coordinates = [float(coordinates), float(coordinates)]

        except ValueError:
            print(f'Error: {coordinates} invalid coordinate/s')
            sys.exit(1)

        return coordinates
    
    else:
        coordinates = [coordinates, coordinates]

        return coordinates


###################### TEST AREA ##########################

# from precip.plotter_functions import *
# from precip.helper_functions import sql_extract_precipitation
# import os
# # from precip.plotter_functions import bar_plotter_2, plot_elninos
# # from matplotlib import pyplot as plt

# date_list = generate_date_list('20000601', '20010603')

# eruption_dates, lalo = extract_volcanoes_info(None, 'Merapi')
# latitude, longitude = adapt_coordinates(lalo[0], lalo[1])

# gpm_dir = os.getenv(scratchDir) + '/gpm_data'

# precipitation = sql_extract_precipitation(latitude, longitude, date_list, gpm_dir)

# precipitation = from_nested_to_float(precipitation)

# sys.exit(0)

#################### END TEST AREA ########################


def main():
    inps = create_parser()

    fig, axes = prompt_subplots(inps)

    return fig, axes

if __name__ == "__main__":
    main()