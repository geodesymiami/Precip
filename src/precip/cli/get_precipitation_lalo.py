#!/usr/bin/env python3

import sys
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import os
from datetime import datetime, date
import argparse
from dateutil.relativedelta import relativedelta
import sys
from precip.plotter_functions import prompt_subplots
from precip.config import jsonVolcano, workDir

EXAMPLE = """
!WARNING for negative values you may need to use the following format: 

--latitude=-10
--latitude=-10.5:-9.5

Date format: YYYYMMDD

Example:
  
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 20190101 20210929
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 --start-date 20190101 --end-date 20210929
  get_precipitation_lalo.py --plot-daily --lalo 19.5:-156.5 20190101 20210929
  get_precipitation_lalo.py --plot-daily --lalo 19.5:-156.5 ---period 20190101:20210929
  get_precipitation_lalo.py --plot-daily --lalo 19.5,-156.5 ---period 20190101,20210929
  get_precipitation_lalo.py --plot-daily 20190101 20210929 --latitude 19.5 --longitude -156.5
  get_precipitation_lalo.py --plot-daily 20190101 20210929 --latitude=19.5 --longitude=-156.5
  get_precipitation_lalo.py --plot-daily 20190101 20210929 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'

  get_precipitation_lalo.py --download
  get_precipitation_lalo.py --download 20190101 20210929
  get_precipitation_lalo.py --period 20190101:20210929
  get_precipitation_lalo.py --download 20190101 20210929 --dir '/home/user/Downloads'

  get_precipitation_lalo.py --volcano 'Cerro Azul'
  
  get_precipitation_lalo.py --list

  get_precipitation_lalo.py --heatmap 20000601 --latitude=-2.11:2.35 --longitude=-92.68:-88.49
  get_precipitation_lalo.py --heatmap 20000601 --latitude 19.5:20.05 --longitude 156.5:158.05 --vlim 0 10
  get_precipitation_lalo.py --heatmap 20000601 --latitude 19.5:20.05 --longitude 156.5:158.05 --vlim 0 10 --interpolate 5
  get_precipitation_lalo.py --heatmap 20000601 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'
  get_precipitation_lalo.py --heatmap 20000601 --latitude=-2.11:2.35 --longitude=-92.68:-88.49 --colorbar jet

  TEMPORARY:
  annual plotter:
  get_precipitation_lalo.py --annual-plotter 'Mauna Loa' --period 20200101:20221231

  bar plotter:
  get_precipitation_lalo.py --bar-plotter 'Mauna Loa' --period 20200101:20221231

  by strength:
  get_precipitation_lalo.py --strength 'Mauna Loa' --period 20200101:20221231

"""

path_data = '/Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)
    
    parser.add_argument('--download', 
                        nargs='*', 
                        metavar=('STARTDATE', 'ENDDATE'),
                        default=None,
                        help='Download data')
    parser.add_argument('--volcano', 
                        nargs=1, 
                        metavar='NAME', 
                        help='Plot eruption dates and precipitation levels')
    parser.add_argument('--plot-daily', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with daily precipitation data')
    parser.add_argument('--plot-weekly', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with weekly precipitation data')
    parser.add_argument('--plot-monthly', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with monthly precipitation data')
    parser.add_argument('--plot-yearly', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with yearly precipitation data')
    parser.add_argument('--start-date', 
                        metavar='YYYYMMDD', 
                        help='Start date of the search')
    parser.add_argument('--end-date', 
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
    parser.add_argument('--heatmap', 
                        nargs='+', 
                        metavar=('DATE, use polygon or latitude/longitude args'), 
                        help='Heat map of precipitation')
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
                        help='Interpolate data')
    parser.add_argument('--isolines',
                        nargs=1,
                        metavar=('LEVELS'),
                        help='Number of isolines to be plotted on the map')
    parser.add_argument('--average', 
                        nargs=1, 
                        metavar=('TIME_PERIOD'), 
                        help='Average data')
    parser.add_argument('--check', 
                        action='store_true', 
                        help='Check if the file is corrupted')
    parser.add_argument('--colorbar', 
                        nargs=1,
                        metavar=('COLORBAR'), 
                        help='Colorbar')
    
    # TODO Schifo da sistemare
    parser.add_argument('--annual-plotter',
                        nargs='*',
                        metavar=('LATITUDE, LONGITUDE, STARTDATE, ENDDATE'),
                        help='Annual plotter')  
    parser.add_argument('--bar-plotter',
                        nargs='*',
                        metavar=('LATITUDE, LONGITUDE, STARTDATE, ENDDATE'),
                        help='Bar plotter')
    parser.add_argument('--strength',
                        nargs='*',
                        metavar=('STRENGTH'),
                        help='Strength of the eruption')

    inps = parser.parse_args()

    if not inps.dir:
        inps.dir = (os.getenv(workDir)) if workDir in os.environ else (os.getenv('HOME'))
        os.environ[workDir] = inps.dir
        inps.dir = inps.dir + '/gpm_data'

    else:
        inps.dir = inps.dir[0]

    if not inps.period:
        inps.start_date = datetime.strptime(inps.start_date[0], '%Y%m%d').date() if inps.start_date else datetime.strptime('20000601', '%Y%m%d').date()
        inps.end_date = datetime.strptime(inps.end_date[0], '%Y%m%d').date() if inps.end_date else datetime.today().date() - relativedelta(days=1)

    else:
        if ':' in inps.period:
            dates = inps.period.split(':')

        elif ',' in inps.period:
            dates = inps.period.split(',')

        elif ' ' in inps.period:
            dates = inps.period.split(' ')

        inps.start_date = datetime.strptime(dates[0], '%Y%m%d').date()
        inps.end_date = datetime.strptime(dates[1], '%Y%m%d').date()

    if inps.download is None:
        pass

    elif len(inps.download) == 0:
        inps.download = datetime.strptime('20000601', '%Y%m%d').date(), (datetime.today().date() - relativedelta(days=1))

    elif len(inps.download) == 1:
        inps.download = inps.download[0], (datetime.today().date() - relativedelta(days=1))

    elif len(inps.download) == 2:
        inps.download = [datetime.strptime(inps.download[0], '%Y%m%d').date(), datetime.strptime(inps.download[1], '%Y%m%d').date()]

    else:
        parser.error("--download requires 0, 1 or 2 arguments")

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
            inps.latitude = [coordinates[0], coordinates[0]]
            inps.longitude = [coordinates[1], coordinates[1]]

    else:
            inps.latitude, inps.longitude = parse_polygon(inps.polygon)

    if inps.plot_daily is not None:
        inps.plot_daily = parse_plot(inps.plot_daily, inps.latitude, inps.longitude, inps.start_date, inps.end_date)

    if inps.plot_weekly is not None:
        inps.plot_weekly = parse_plot(inps.plot_weekly, inps.latitude, inps.longitude, inps.start_date, inps.end_date)

    if inps.plot_monthly is not None:
        inps.plot_monthly = parse_plot(inps.plot_monthly, inps.latitude, inps.longitude, inps.start_date, inps.end_date)

    if inps.plot_yearly is not None:
        inps.plot_yearly = parse_plot(inps.plot_yearly, inps.latitude, inps.longitude, inps.start_date, inps.end_date)    

    if inps.heatmap is not None:
        if len(inps.heatmap) == 0:
            if inps.end_date:
                inps.heatmap = inps.start_date, inps.end_date
            
            else:
                inps.heatmap = inps.start_date, None

        elif len(inps.heatmap) == 1:
            try:
                inps.heatmap = datetime.strptime(inps.heatmap[0], '%Y%m%d').date(), None

            except ValueError:
                print('Error: Date format not valid, if only 1 argument is given, it must be in the format YYYYMMDD')
                sys.exit(1)

        elif len(inps.heatmap) == 2:
            try:
                inps.heatmap = datetime.strptime(inps.heatmap[0], '%Y%m%d').date(), datetime.strptime(inps.heatmap[1], '%Y%m%d').date()
                
                if inps.heatmap[1]:
                    inps.average = None
            
            except ValueError:
                print('Error: Date format not valid, if only 1 argument is given, it must be in the format YYYYMMDD')
                sys.exit(1)
     
        else:
            parser.error("--heatmap requires 0, 1 or 2 arguments")

    if not inps.colorbar:
        inps.colorbar = 'viridis'

    ####################### TODO to format #######################
    if inps.annual_plotter is not None:
        if len(inps.annual_plotter) == 0:
            parser.error("--annual-plotter requires at least VOLCANO")

        elif len(inps.annual_plotter) == 1:
            inps.annual_plotter = inps.annual_plotter[0], 3, 3, inps.start_date, inps.end_date

        elif len(inps.annual_plotter) == 2:
            inps.annual_plotter = inps.annual_plotter[0], int(inps.annual_plotter[1]), 3, inps.start_date, inps.end_date

        elif len(inps.annual_plotter) == 3:
            inps.annual_plotter = inps.annual_plotter[0], int(inps.annual_plotter[1]), int(inps.annual_plotter[2]), inps.start_date, inps.end_date

    if inps.bar_plotter is not None:
        if len(inps.bar_plotter) == 0:
            parser.error("--bar-plotter requires at least VOLCANO")

        elif len(inps.bar_plotter) == 1:
            inps.bar_plotter = inps.bar_plotter[0], 3, 3, inps.start_date, inps.end_date

        elif len(inps.bar_plotter) == 2:
            inps.bar_plotter = inps.bar_plotter[0], int(inps.bar_plotter[1]), 3, inps.start_date, inps.end_date

        elif len(inps.bar_plotter) == 3:
            inps.bar_plotter = inps.bar_plotter[0], int(inps.bar_plotter[1]), int(inps.bar_plotter[2]), inps.start_date, inps.end_date

    if inps.strength is not None:
        if len(inps.strength) == 0:
            parser.error("--strength requires at least VOLCANO")

        elif len(inps.strength) == 1:
            inps.strength = inps.strength[0], 3, 3, inps.start_date, inps.end_date

        elif len(inps.strength) == 2:
            inps.strength = inps.strength[0], int(inps.strength[1]), 3, inps.start_date, inps.end_date

        elif len(inps.strength) == 3:
            inps.strength = inps.strength[0], int(inps.strength[1]), int(inps.strength[2]), inps.start_date, inps.end_date

    ####################### END to format #######################

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


def parse_plot(plot, latitudes, longitudes, start_date=None, end_date=None):
    """
    Parses the plot parameters for precipitation data.

    Args:
        plot (list): The plot input parameters.
        latitudes (list): The latitude values.
        longitudes (list): The longitude values.
        start_date (datetime, optional): The start date. Defaults to None.
        end_date (datetime, optional): The end date. Defaults to None.

    Returns:
        list: The parsed plot parameters.
    """
    if len(plot) == 0: 
            plot = [latitudes[0], longitudes[0], start_date, end_date]
    
    elif len(plot) == 1:
        print("--plot-[daily, weekly, monthly, yearly] requires at least LATITUDE LONGITUDE arguments \n"
                     " --plot-daily LATITUDE LONGITUDE arguments \n"
                     " --plot-weekly --latitude LATITUDE -- longitude LONGITUDE \n"
                     " START_DATE END_DATE are optional")
        sys.exit(1)

    elif len(plot) == 2:
        if latitudes and longitudes:
            plot = [latitudes[0], longitudes[0], datetime.strptime(plot[0], "%Y%m%d"), datetime.strptime(plot[1], "%Y%m%d")]

        elif start_date and end_date:
            plot = [parse_coordinates(plot[0]), parse_coordinates(plot[1]), start_date[0], end_date[0]]

        else:
            print("--plot-[daily, weekly, monthly, yearly] requires at least LATITUDE LONGITUDE arguments \n"
                     " --plot-daily LATITUDE LONGITUDE arguments \n"
                     " --plot-weekly --latitude LATITUDE -- longitude LONGITUDE \n"
                     " START_DATE END_DATE are optional")
            sys.exit(1)

    elif len(plot) == 3:
            print("--plot-[daily, weekly, monthly, yearly] requires at least LATITUDE LONGITUDE arguments \n"
                     "Three arguments are ambiguous")
            sys.exit(1)

    elif len(plot) == 4:
        try:
            plot = [parse_coordinates(plot[0]), parse_coordinates(plot[1]), datetime.strptime(plot[2], "%Y%m%d"), datetime.strptime(plot[3], "%Y%m%d")]

        except ValueError:
            plot = [datetime.strptime(plot[0], "%Y%m%d"), datetime.strptime(plot[1], "%Y%m%d"), parse_coordinates(plot[2]), parse_coordinates(plot[3])]

        except Exception as e:
            print(e)
            sys.exit(1)

    return plot



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
    coordinates = coordinates.replace("'", '').replace('"', '')

    try:
        if ',' in coordinates:
            coordinates = coordinates.split(',')
            coordinates = [float(i) for i in coordinates]

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


###################### TEST AREA ##########################

# from precip.plotter_functions import *

# # la, lo = '19.5:20.05', '156.5:158.05'
# # la , lo = parse_polygon('POLYGON((-93.7194 -2.2784,-87.4571 -2.2784,-87.4571 2.6319,-93.7194 2.6319,-93.7194 -2.2784))')
# la, lo = '19.5', '-156.5'
# la, lo = adapt_coordinates(la, lo)
# date_list = generate_date_list('20150101', '20220101')

# workDir = '/Users/giacomo/onedrive/scratch'
# prec = create_map(la, lo, date_list, workDir + '/gpm_data')
# eruptions, _, _ = extract_volcanoes_info(workDir + '/' + jsonVolcano, 'Wolf')
# # bar_plot(prec, la, lo)
# # annual_plotter(prec, 3, 3, eruptions)
# # map_precipitation(prec, lo, la, ['2000-06-01'], workDir + '/gpm_data', 'jet',levels=1)
# bar_plotter(prec, 3, 3, eruptions)

# sys.exit(0)

#################### END TEST AREA ########################


def main():
    inps = create_parser()

    prompt_subplots(inps, jsonVolcano)

if __name__ == "__main__":
    main()

# sys.exit(0)