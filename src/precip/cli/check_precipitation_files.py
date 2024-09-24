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
from precip.objects.classes.providers.jetstream import JetStream
from precip.objects.classes.file_manager.cloud_file_manager import CloudFileManager
from precip.objects.classes.file_manager.local_file_manager import LocalFileManager
from precip.objects.classes.credentials_settings.credentials import PrecipVMCredentials


PRECIP_DIR = os.getenv('PRECIP_DIR')
EXAMPLE = f"""
Check if the downloaded files are corrupted:
    check_precipitation_files.py

Check if the downloaded files are corrupted on cloud server:
    check_precipitation_files.py --use-ssh

"""


def create_parser(iargs=None, namespace=None):
    """ 
    Creates command line argument parser object.

    Args:
        iargs (list): List of command line arguments (default: None)
        namespace (argparse.Namespace): Namespace object to store parsed arguments (default: None)

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Check if precipitation files from GPM dataset are corrupted',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('-ssh', '--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')
    parser.add_argument('-d', '--dir',
                        type=str,
                        default=PRECIP_DIR,
                        help='Specify path to download the data, default is %(default)s')


    inps = parser.parse_args(iargs, namespace)


    return inps


def check_files(inps):
    """
    Check if precipitation files are corrupted.

    Args:
        inps (argparse.Namespace): Parsed command line arguments
    """
    if inps.use_ssh:
        jtstream = JetStream(PrecipVMCredentials())
        CloudFileManager(jtstream).check_files()

    else:
        local = LocalFileManager(inps.dir)
        local.check_files()



def main(iargs=None, namespace=None):
    """
    Main function to check precipitation files.

    Args:
        iargs (list): List of command line arguments (default: None)
        namespace (argparse.Namespace): Namespace object to store parsed arguments (default: None)
    """
    inps = create_parser(iargs, namespace)

    check_files(inps)




if __name__ == "__main__":
    main()