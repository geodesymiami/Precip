#!/usr/bin/env python3

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from precip.objects.classes.configuration import PlotConfiguration
from precip.objects.classes.plotters.plotters import MapPlotter, BarPlotter, AnnualPlotter
from precip.cli.plot_precipitation import create_parser
from precip.utils.argument_parsers import add_save_arguments
from precip.data_extraction_functions import get_precipitation_data
import pandas as pd

SCRATCH_DIR = os.environ.get('SCRATCHDIR')
VOLCANO_FILE = os.environ.get('PRECIP_HOME') + '/src/precip/Holocene_Volcanoes_precip_cfg.xlsx'
DEFAULT_STYLES = ['map', 'bar', 'annual', 'strength']
# DEFAULT_STYLES = ['bar', 'annual', 'strength']        # FA 7/2025  map gives problems woth GMT
BINS = [2, 3, 4]

def get_volcanoes():
    df = pd.read_excel(VOLCANO_FILE, skiprows=1)
    df = df[df['Precip'] != False]

    volcano_dict = {
        r['Volcano Name'] : {
            'id': r['Volcano Number']
        } for _, r in df.iterrows()}

    return volcano_dict

def main(iargs=None, namespace=None):
    # TODO Import only the parsers that you need from .utils
    args = create_parser(iargs, namespace)

    plot_dir = os.path.join(os.getenv('SCRATCHDIR'), 'precip_plots')
    os.makedirs(plot_dir, exist_ok=True)

    volcanoes = get_volcanoes()

    for volcano, info in volcanoes.items():
        id = info['id']
        volcano_dir = os.path.join(plot_dir, str(id))

        if os.path.exists(volcano_dir) or (volcano == 'Cotopaxi'):
            print('skipping ', volcano, ' ', volcano_dir)
            continue

        for bins in BINS:
            os.makedirs(volcano_dir, exist_ok=True)
            iargs = ['--volcano-name', volcano, '--bins', str(bins), "--no-show", "--save","--outdir", volcano_dir]
            iargs = iargs + sys.argv[1:]
            args = create_parser(iargs, namespace)


            # TODO Try to force the style arg into the Plotter Objects
            args.style = 'bar'
            bar_config = PlotConfiguration(args)
            args.style = 'annual'
            annual_config = PlotConfiguration(args)

            precipitation = get_precipitation_data(bar_config)

            fig = plt.figure(constrained_layout=True)
            main_gs = gridspec.GridSpec(1, 1, figure=fig)
            BarPlotter(fig, main_gs[0], bar_config).plot(precipitation)

            fig = plt.figure(constrained_layout=True)
            main_gs = gridspec.GridSpec(1, 1, figure=fig)
            AnnualPlotter(fig, main_gs[0], annual_config).plot(precipitation)

        args.style = 'map'
        map_config = PlotConfiguration(args)
        map_precipitation = get_precipitation_data(map_config)

        fig = plt.figure(constrained_layout=True)
        main_gs = gridspec.GridSpec(1, 1, figure=fig)
        MapPlotter(fig, main_gs[0], map_config).plot(map_precipitation)

        sys.exit()





if __name__ == '__main__':
    main()