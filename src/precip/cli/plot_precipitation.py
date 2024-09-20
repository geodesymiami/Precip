#!/usr/bin/env python3

import os
import argparse
from datetime import datetime
from precip.objects.classes.configuration import PlotConfiguration
from precip.objects.classes.plotters.plotters import MapPlotter, BarPlotter, AnnualPlotter
from matplotlib import pyplot as plt
from matplotlib import gridspec
from precip.data_extraction_functions import handle_data_functions, get_precipitation_data
from precip.cli.utils.argument_parsers import add_plot_parameters_arguments, add_date_arguments, add_location_arguments, add_save_arguments, add_map_parameters_arguments
from precip.config import END_DATE,START_DATE

# TODO Add proper CITATION for GPM data and Volcano data
PRECIP_DIR = os.getenv('PRECIP_DIR')

EXAMPLE = f"""
Date format: YYYYMMDD

Example:

Plot bar style for Merapi volcano from {START_DATE} to {END_DATE} (change values in config.py) with 3 color/s and 30 days (default is 90) rolling window:
    plot_precipitation.py Merapi --style bar --roll 30 --bins 3 --log

Plot bar style at specific location from 2019-01-01 to 2021-09-29 with 1 color/s (default) and 90 days (default) rolling window, add El Nino/La Nina event, save it in specific folder:
    plot_precipitation.py --style bar --lalo 19.5,-156.5 --period 20190101:20210929 --elnino --outdir path/to/dir

Plot strength style for Merapi volcano with 1 color/s (default) and 90 days (default) rolling window; don't show plot and save it in current folder:
    plot_precipitation.py Merapi --style strength --period 20190101:20210929 --no-show --save

Plot annual style at specific location from 2019-01-01 to 2021-09-29 with 2 color/s and 10 days rolling window; add events on 2020-09-29 and 2021-09-29:
    plot_precipitation.py --style annual --start-date 20190101 --end-date 20210929 --latitude 19.5 --longitude -156.5 --roll 10 --bins 2 --add-event 20200929 20210929

Plot msp style at specific location from {START_DATE} (default) to 2021-09-29:
    plot_precipitation.py --style map --end-date 20210929 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'

Plot map style of Merapi with 3 levels (default is 1) of BLACK isolines (default is white), colorbar 'RdBu' (default is 'viridis'):
    plot_precipitation.py Merapi --style map --isolines 3 --isolines-color black --colorbar 'RdBu'

Plot map style of Merapi with precipitation values between -3 and 3, and interpolate:
    plot_precipitation.py Merapi --style map --vlim -3 3 --interpolate 3

Download whole dataset in the default directory $PRECIP_DIR ({os.getenv('PRECIP_DIR')}):
    plot_precipitation.py --download

Download dataset from 2019-01-01 to 2021-09-29 in the specific directory on cloud:
    plot_precipitation.py --download --period 20190101:20210929 --use-ssh

Check if the downloaded files are corrupted:
    plot_precipitation.py --check

List all volcanoes from the json file/API:
    plot_precipitation.py --list

"""


def create_parser(iargs=None, namespace=None):
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('name',
                        nargs='?',
                        type=str,
                        help='Volcano name')
    parser.add_argument('--volcano-name',
                        nargs=1,
                        type=str,
                        metavar=('NAME'),
                        help='Name of the volcano')
    parser.add_argument('--style',
                        choices=['daily','weekly','monthly','yearly','map','bar','annual','strength'],
                        help='Choose plot type')
    parser.add_argument('--download',
                        action='store_true',
                        help='Use ssh')
    parser.add_argument('--list',
                        action='store_true',
                        help='List volcanoes')
    parser.add_argument('--check',
                        action='store_true',
                        help='Check if the file is corrupted')
    parser.add_argument('--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')
    parser.add_argument('--parallel',
                        type=int,
                        default=5,
                        help='Number of parallel downloads')

    parser = add_location_arguments(parser)
    parser = add_date_arguments(parser)
    parser = add_plot_parameters_arguments(parser)
    parser = add_map_parameters_arguments(parser)
    parser = add_save_arguments(parser)

    inps = parser.parse_args(iargs, namespace)

    #exit()
    # FA: create_parser has much too much.
    ############################ POSITIONAL ARGUMENTS ############################

    # FA: using len(inps.positional) looks strange. I would expect this is handled better by argparse?
    # FA: suggest to assign the positional argument to volcano_name in argparse. If the number of positional arguments is zero:  inps.latitude, inps.longitude = get_latitude_longitude(inps)
    # if len(inps.name) == 1:

    #     # FA: this should be in a function
    #     # Unfortunately this can never work if we pass the coordinates since negative numbers are viewed as options
    #     if any(char.isdigit() for char in inps.name):
    #         if 'POLYGON' in inps.name:
    #             inps.latitude, inps.longitude = parse_polygon(inps.name[0])

    #         else:
    #             coordinates = parse_coordinates(inps.name[0])
    #             inps.latitude = parse_coordinates(coordinates[0])
    #             inps.longitude = parse_coordinates(coordinates[1])

    # inps.volcano_name = inps.name
    # Same issue here
    # if len(inps.positional) == 2:
    #     inps.latitude = parse_coordinates(inps.positional[0])

    #     inps.longitude = parse_coordinates(inps.positional[1])

    ###############################################################################
    if inps.name:
        inps.volcano_name = [inps.name]

    inps.dir = PRECIP_DIR

    # FA: Assuming that inps.start_date and inps.end_date will be later consider function: inps.start_date, inps.end_date=get_processing_dates(inps)
    if not inps.period:
        inps.start_date = datetime.strptime(inps.start_date, '%Y%m%d').date()

        #End date subject to variations, check for alternatives on config.py
        inps.end_date = datetime.strptime(inps.end_date, '%Y%m%d').date()

    else:
        if ':' in inps.period:
            dates = inps.period.split(':')
        # TODO not sure if this is to be removed
        elif ',' in inps.period:
            dates = inps.period.split(',')

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
            coordinates = parse_coordinates(inps.lalo)
            inps.latitude = parse_coordinates(coordinates[0])
            inps.longitude = parse_coordinates(coordinates[1])
            inps.latitude, inps.longitude = [min(inps.latitude), max(inps.latitude)], [min(inps.longitude), max(inps.longitude)]

    else:
            inps.latitude, inps.longitude = parse_polygon(inps.polygon)

    # FA: Not sure why to introduce inps.average = 'W'. You can use use 'if inps.style == 'weekly'' later in the code?
    if inps.style == 'weekly':
        inps.average = 'W'

    elif inps.style == 'monthly':
        inps.average = 'M'

    elif inps.style == 'yearly':
        inps.average = 'Y'

    elif inps.style == 'annual':
        inps.average = 'D'

    elif inps.style == 'map':
        inps.add_event = None

    if inps.add_event:
        try:
            inps.add_event = tuple(datetime.strptime(date_string, '%Y-%m-%d').date() for date_string in inps.add_event)

        except ValueError:
            try:
                inps.add_event = tuple(datetime.strptime(date_string, '%Y%m%d').date() for date_string in inps.add_event)

            except ValueError:
                msg = 'Date format not valid, it must be in the format YYYYMMDD or YYYY-MM-DD'
                raise ValueError(msg)

    if not inps.bins:
        inps.bins = 4 if inps.bins > 4 else inps.bins

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
            msg=f'Error: {coordinates} invalid coordinate/s'
            raise ValueError(msg)

        return coordinates

    else:
        coordinates = [coordinates, coordinates]

        return coordinates


###################### TEST AREA ##########################
# from matplotlib import pyplot as plt
# from matplotlib import gridspec
# import sys
# from precip.plotter_functions import get_precipitation_data
# from precip.helper_functions import generate_date_list, adapt_coordinates
# from precip.objects.configuration import PlotConfiguration
# from precip.objects.plotters import MapPlotter, BarPlotter, AnnualPlotter
# from precip.manager_functions import handle_plotters

# def main(iargs=None, namespace=None, ax=None):
#     inps = create_parser(iargs, namespace)
#     inps.dir = PRECIP_DIR
#     os.makedirs(PRECIP_DIR, exist_ok=True)

#     if not inps.show_flag:
#         # plt.switch_backend('Agg')
#         pass


#     fig = plt.figure(constrained_layout=True)
#     main_gs = gridspec.GridSpec(2, 1, figure=fig)

#     fig = handle_plotters(inps, main_gs[0], fig)

#     inps.style = 'annual'

#     fig = handle_plotters(inps, main_gs[1], fig)

#     plt.show()


# if __name__ == "__main__":
#     main()

#sys.exit(0)

#################### END TEST AREA ########################

def main(iargs=None, namespace=None, main_gs=None, fig=None):

    inps = create_parser(iargs, namespace)

    os.makedirs(PRECIP_DIR, exist_ok=True)

    # TODO move all the functions in cli
    handle_data_functions(inps)

    input_config = PlotConfiguration(inps)
    precipitation = get_precipitation_data(input_config)

    if main_gs is None:
        fig = plt.figure(constrained_layout=True)
        main_gs = gridspec.GridSpec(1, 1, figure=fig)
        main_gs = main_gs[0]

    if inps.style == 'map':
        graph = MapPlotter(fig, main_gs, input_config)

    if inps.style in ['daily', 'weekly', 'monthly', 'bar', 'strength']:
        graph = BarPlotter(fig, main_gs, input_config)

    if inps.style == 'annual':
        graph = AnnualPlotter(fig, main_gs, input_config)

    graph.plot(precipitation)

    return fig

if __name__ == "__main__":
    main()
