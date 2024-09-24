#!/usr/bin/env python3

#################################################################
# Data extracted from:                                          #
# Global Volcanism Program, 2024.                               #
# [Database] Volcanoes of the World (v. 5.2.3; 20 Sep 2024).    #
# Distributed by Smithsonian Institution, compiled by Venzke, E.#
# https://doi.org/10.5479/si.GVP.VOTW5-2024.5.2                 #
# Source: https://volcano.si.edu/                               #
#################################################################

# Global Volcanism Program, 2024. [Database] Volcanoes of the World (v. 5.2.3; 20 Sep 2024). Distributed by Smithsonian Institution, compiled by Venzke, E. https://doi.org/10.5479/si.GVP.VOTW5-2024.5.2

from precip.volcano_functions import volcanoes_list
from precip.config import JSON_VOLCANO
import argparse
import os


SCRATCHDIR = os.getenv('SCRATCHDIR')
EXAMPLE = f"""
List volcanoes

list_volcanoes.py

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
        description='List volcanoes from API or local JSON file at Global Volcanism Program, Smithsonian Institutionwebsite: https://volcano.si.edu/',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('-d', '--dir',
                        type=str,
                        default=SCRATCHDIR,
                        help='Specify path to look for the json file, default is %(default)s')

    inps = parser.parse_args(iargs, namespace)


    return inps


def main(iargs=None, namespace=None):
    """
    Main function to check precipitation files.

    Args:
        iargs (list): List of command line arguments (default: None)
        namespace (argparse.Namespace): Namespace object to store parsed arguments (default: None)
    """
    inps = create_parser(iargs, namespace)

    volcanoes_list(os.path.join(inps.dir, JSON_VOLCANO))


if __name__ == "__main__":
    main()