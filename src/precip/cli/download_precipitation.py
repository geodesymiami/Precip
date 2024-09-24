#!/usr/bin/env python3

#############################################################################
# Data from:                                                                #
# Huffman, G.J., E.F. Stocker, D.T. Bolvin, E.J. Nelkin, Jackson Tan (2023),#
# GPM IMERG Final Precipitation L3 1 day 0.1 degree x 0.1 degree V07,       #
# GPM IMERG Late Precipitation L3 1 day 0.1 degree x 0.1 degree V06,        #
# Edited by Andrey Savtchenko, Greenbelt, MD,                               #
# Goddard Earth Sciences Data and Information Services Center (GES DISC),   #
# Accessed: [Data Access Date], 10.5067/GPM/IMERGDF/DAY/07                  #
#############################################################################

import os
import argparse
from datetime import datetime
from precip.objects.classes.providers.jetstream import JetStream
from precip.objects.classes.file_manager.cloud_file_manager import CloudFileManager
from precip.objects.classes.file_manager.local_file_manager import LocalFileManager
from precip.objects.classes.credentials_settings.credentials import PrecipVMCredentials
from precip.helper_functions import generate_date_list
from precip.utils.argument_parsers import add_date_arguments

# TODO Add proper CITATION for GPM data and Volcano data
PRECIP_DIR = os.getenv('PRECIP_DIR')
EXAMPLE = f"""
Date format: YYYYMMDD

Download whole dataset in the default directory $PRECIP_DIR ({os.getenv('PRECIP_DIR')}):
    download_precipitation.py

Download whole dataset in the specified directory:
    download_precipitation.py --dir /path/to/directory

Download dataset from 2019-01-01 to 2021-09-29 in the specific directory on cloud:
    download_precipitation.py --period 20190101:20210929 --use-ssh

"""


def create_parser(iargs=None, namespace=None):
    """Creates command line argument parser object.

    Args:
        iargs (list): List of command line arguments (default: None).
        namespace (argparse.Namespace): Namespace object to store parsed arguments (default: None).

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description='Download precipitation data from GPM dataset',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('-ssh', '--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')
    parser.add_argument('-p', '--parallel',
                        type=int,
                        default=5,
                        help='Number of parallel downloads')
    parser.add_argument('-d', '--dir',
                        type=str,
                        default=PRECIP_DIR,
                        help='Specify path to download the data, default is %(default)s')


    parser = add_date_arguments(parser)

    inps = parser.parse_args(iargs, namespace)

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

    return inps


def download_precipitation(inps):
    """Downloads precipitation data based on the provided command line arguments.

    Args:
        inps (argparse.Namespace): Parsed command line arguments.
    """

    if inps.use_ssh:
        jtstream = JetStream(PrecipVMCredentials())
        CloudFileManager(jtstream).download(inps.date_list, inps.parallel)

    else:
        local = LocalFileManager(inps.dir)
        local.download(inps.date_list, inps.parallel)



def main(iargs=None, namespace=None, date_list=None):
    """Main function to execute the script.

    Args:
        iargs (list): List of command line arguments (default: None).
        namespace (argparse.Namespace): Namespace object to store parsed arguments (default: None).
        date_list (list): List of dates to process (default: None).
    """

    inps = create_parser(iargs, namespace)

    if date_list is None:
        inps.date_list = generate_date_list(inps.start_date, inps.end_date)

    else:
        inps.date_list = date_list

    download_precipitation(inps)


if __name__ == "__main__":
    main()