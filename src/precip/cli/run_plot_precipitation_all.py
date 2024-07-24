#!/usr/bin/env python3

from itertools import product
import os
import argparse
import matplotlib.pyplot as plt
from precip.cli import plot_precipitation
import pandas as pd

# This is needed to run on a server without a display
import matplotlib
matplotlib.use('Agg')

SCRATCH_DIR = os.environ.get('SCRATCHDIR')
VOLCANO_FILE = os.environ.get('PRECIP_HOME') + '/src/precip/Holocene_Volcanoes_precip_cfg..xlsx'
DEFAULT_STYLES = ['map', 'bar', 'annual', 'strength']
# DEFAULT_STYLES = ['bar', 'annual', 'strength']        # FA 7/2025  map gives problems woth GMT
BINS = [2, 3, 4]

EXAMPLES = """
Examples:

Plot all styles for all volcanoes:
    run_plot_precipitation_all.py --period 20060101:20070101

Plot all volcanoes with a different plot directory:
    run_plot_precipitation_all.py --plot-dir .
    run_plot_precipitation_all.py --plot-dir /path/to/plot_dir

Plot with a different volcano file:
    run_plot_precipitation_all.py --volcano-file /path/to/volcano_file.xlsx

Plot with different styles:
    run_plot_precipitation_all.py --styles map bar

plot_precipitation --help for more options
"""

def create_parser():
    synopsis = 'Wrapper tool to run plot_precipitation with multiple styles and all volcanoes'
    parser = argparse.ArgumentParser(
        description=synopsis,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLES
    )
    parser.add_argument('--volcano-file',
                        default=VOLCANO_FILE,
                        metavar='',
                        help='File with volcano names (default: %(default)s)')
    parser.add_argument('--plot-dir',
                        default='/data/',
                        help='Directory to save plots (default: %(default)s)')
    parser.add_argument('--styles',
                        nargs='+',
                        default=DEFAULT_STYLES,
                        help='List of plot styles to use (default: %(default)s)')
    return parser

def get_volcanoes():
    df = pd.read_excel(VOLCANO_FILE, skiprows=1)
    df = df[df['Precip'] != False]

    volcano_dict = {
        r['Volcano Name'] : {
            'id': r['Volcano Number']
        } for _, r in df.iterrows()}

    return volcano_dict


def main():
    parser = create_parser()
    args, unknown_args = parser.parse_known_args()

    plot_dir = os.path.join(args.plot_dir, 'precip_plots')
    os.makedirs(plot_dir, exist_ok=True)

    volcanoes = get_volcanoes()
    failures = {}
    i = 0

    plot_params = [(style, i) for style, i in product(args.styles, BINS) if not (style == 'map' and i > 1)]

    for volcano, info in volcanoes.items():
        id = info['id']
        volcano_dir = os.path.join(plot_dir, str(id))
        if os.path.exists(volcano_dir) or (volcano == 'Cotopaxi'):
            print('skipping ', volcano, ' ', volcano_dir)
            continue
        for style, bins in plot_params:
            i+=1
            inps = argparse.Namespace(style=style,
                                      volcano_name=[volcano],
                                      no_show=True,
                                      save_flag=False,
                                      bins=bins)


            png_path = os.path.join(volcano_dir, f'{id}_{style}_bin_{bins}.png')
            print(volcano, ' ', png_path)
            try:
                plot_precipitation.main(unknown_args, inps)
                os.makedirs(volcano_dir, exist_ok=True)
                plt.savefig(png_path)
                plt.close()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                failures[png_path] = e

    print('#'*50)
    print(f'Failed to plot for the following volcanoes: {len(failures)}/{i}')
    print()
    # print(failures.keys())
    print(failures)

if __name__ == '__main__':
    main()
