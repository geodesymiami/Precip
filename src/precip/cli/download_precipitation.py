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
    plot_precipitation.py --download

Download dataset from 2019-01-01 to 2021-09-29 in the specific directory on cloud:
    plot_precipitation.py --download --period 20190101:20210929 --use-ssh

"""


def create_parser(iargs=None, namespace=None):
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('--download',
                        action='store_true',
                        help='Use ssh')

    parser.add_argument('--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')
    parser.add_argument('--parallel',
                        type=int,
                        default=5,
                        help='Number of parallel downloads')


    parser = add_date_arguments(parser)

    inps = parser.parse_args(iargs, namespace)

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


def download_precipitation(inps):
    date_list = generate_date_list(inps.start_date, inps.end_date, inps.average)

    if inps.use_ssh:
        jtstream = JetStream(PrecipVMCredentials())
        CloudFileManager(jtstream).download(date_list)

    else:
        local = LocalFileManager(inps.dir)
        local.download(date_list)



def main(iargs=None, namespace=None, main_gs=None, fig=None):

    inps = create_parser(iargs, namespace)

    download_precipitation(inps)


if __name__ == "__main__":
    main()