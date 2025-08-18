import os
from precip.config import START_DATE, END_DATE


def add_date_arguments(parser):
    """
    Argument parser for the date range of the search.

    Args:
        parser (argparse.ArgumentParser): The argument parser object.

    Returns:
        argparse.ArgumentParser: The argument parser object with added date arguments.
    """
    date = parser.add_argument_group('Date range of the search')
    date.add_argument('--start-date',
                        nargs='?',
                        default=START_DATE,
                        metavar='YYYYMMDD',
                        help='Start date of the search, default is %(default)s')
    date.add_argument('--end-date',
                        nargs='?',
                        default=END_DATE,
                        metavar='YYYYMMDD',
                        help='End date of the search, default is %(default)s')
    date.add_argument('--period',
                        nargs='?',
                        metavar='YYYYMMDD:YYYYMMDD, YYYYMMDD,YYYYMMDD',
                        help='Period of the search')

    return parser


def add_location_arguments(parser):
    """
    Argument parser for the location of the volcano or area of interest.

    Args:
        parser (argparse.ArgumentParser): The argument parser object.

    Returns:
        argparse.ArgumentParser: The argument parser object with added location arguments.
    """
    location = parser.add_argument_group('Location of the volcano or area of interest')
    location.add_argument('--latitude',
                        nargs='*',
                        metavar=('LATITUDE or LATITUDE:LATITUDE'),
                        help='Latitude')
    location.add_argument('--longitude',
                        nargs='*',
                        metavar=('LONGITUDE or LONGITUDE:LONGITUDE'),
                        help='Longitude')
    location.add_argument('--lalo',
                        nargs='?',
                        metavar=('LATITUDE,LONGITUDE or LATITUDE:LATITUDE,LONGITUDE:LONGITUDE'),
                        help='Latitude and longitude')
    location.add_argument('--polygon',
                        metavar='POLYGON',
                        help='Polygon of the wanted area (Format from ASF Vertex Tool https://search.asf.alaska.edu/#/)')

    return parser


def add_plot_parameters_arguments(parser):
    """
    Argument parser for the plot parameters.

    Args:
        parser (argparse.ArgumentParser): The argument parser object.

    Returns:
        argparse.ArgumentParser: The argument parser object with added plot parameters arguments.
    """
    plot_parameters = parser.add_argument_group('Plot parameters')
    plot_parameters.add_argument('--log',
                        action='store_true',
                        help='Enable logaritmic scale')
    plot_parameters.add_argument('--bins',
                        type=int,
                        metavar=('BINS'),
                        default=1,
                        help='Number of bins for the histogram (default: %(default)s)')
    plot_parameters.add_argument('--roll',
                        type=int,
                        metavar=('ROLL'),
                        default=90,
                        help='Rolling average (default: %(default)s)')
    plot_parameters.add_argument('--elnino',
                        action='store_true',
                        dest = 'elnino',
                        help='Plot Nino/Nina events')
    plot_parameters.add_argument('--no-show',
                        dest='show_flag',
                        action='store_false',
                        default=True,
                        help='Do not show the plot')

    return parser


def add_map_parameters_arguments(parser):
    """
    Argument parser for the map parameters.

    Args:
        parser (argparse.ArgumentParser): The argument parser object.

    Returns:
        argparse.ArgumentParser: The argument parser object with added map parameters arguments.
    """
    map_parameters = parser.add_argument_group('Map parameters')
    map_parameters.add_argument('--vlim',
                        nargs=2,
                        metavar=('VMIN', 'VMAX'),
                        help='Velocity limit for the colorbar')
    map_parameters.add_argument('--interpolate',
                        metavar='GRANULARITY',
                        type=int,
                        help='Interpolate data')
    map_parameters.add_argument('--isolines',
                        nargs='?',
                        default=0,
                        type=int,
                        metavar='LEVELS',
                        help='Number of isolines to be plotted on the map, default is %(default)s')
    map_parameters.add_argument('--cumulate',
                        action='store_true',
                        help='Cumulate data')
    map_parameters.add_argument('--average',
                        choices={'D','W','M','Y', None},
                        nargs='?',
                        default=None,
                        const='D',
                        metavar='TIME_PERIOD',
                        help='Average data, default is daily')
    map_parameters.add_argument('--colorbar',
                        default='viridis',
                        metavar='COLORBAR',
                        help='Colorbar, default is %(default)s')
    map_parameters.add_argument('--isolines-color',
                        dest='iso_color',
                        type=str,
                        default='white',
                        metavar='COLOR',
                        help='Color of contour lines, default is %(default)s')

    return parser


def add_save_arguments(parser):
    """
    Argument parser for the save options.

    Args:
        parser (argparse.ArgumentParser): The argument parser object.

    Returns:
        argparse.ArgumentParser: The argument parser object with added save arguments.
    """
    save = parser.add_argument_group('Save options')
    save.add_argument('--save',
                      choices={'volcano-name', 'volcano-id', None},
                      dest='save',
                      default=None,
                      const='volcano-name',
                      nargs='?',
                      help='Save the plot. If --save is provided without a value, default is %(const)s.')
    save.add_argument('--outdir',
                        type=str,
                        default=os.getcwd(),
                        metavar='PATH',
                        help='Folder to save the plot, default is %(default)s')

    return parser