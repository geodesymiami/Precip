#!/usr/bin/env python3

from precip.cli import plot_precipitation
import argparse

DEFAULT_STYLES = ['map', 'bar', 'annual', 'strength']

EXAMPLES = """
Examples:

Plot all styles for a volcano:
    get_all.py Merapi --period=20060101:20070101

Plot all styles for a volcano with two styles:
    get_all.py Merapi --period=20060101:20070101 --styles map bar

Plot all stles and pass additional arguments to plot_precipitation:
    get_all.py Merapi --period=20060101:20070101 --styles map bar --no-show
    get_all.py Merapi --period=20060101:20070101 --styles map bar --dir '/home/user/Downloads'

plot_precipitation --help for more options
"""


def create_parser():
    parser = argparse.ArgumentParser(
        description='Wrapper tool to run plot_precipitation for a volcano with muliple plot styles',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLES
    )
    parser.add_argument('--styles',
                        nargs='+',
                        default=DEFAULT_STYLES,
                        help='List of plot styles to use (default: %(default)s)')
    return parser

def main():
    parser = create_parser()
    args, unknown_args = parser.parse_known_args()
    for style in args.styles:
        inps = argparse.Namespace(style=style)
        plot_precipitation.main(unknown_args, inps)

if __name__ == '__main__':
    main()
