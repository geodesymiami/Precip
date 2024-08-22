from matplotlib import pyplot as plt
import pygmt
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from precip.objects.configuration import Configuration
from precip.plotter_functions import weekly_monthly_yearly_precipitation, interpolate_map


class Plotter(ABC):
    @abstractmethod
    def plot(self):
        pass


class MapPlotter(Plotter):
    def __init__(self, ax, config: Configuration):
        self.ax = ax
        self.config = config


    def plot(self, precipitation):
        precipitation = self.modify_dataframe(precipitation)

        if type(precipitation) == pd.DataFrame:
            precip = precipitation.get('Precipitation')[0][0]

        elif type(precipitation) == dict:
            precip = precipitation[self.config.date_list[0].strftime('%Y-%m-%d')]

        else:
            precip = precipitation

        precip = np.flip(precip.transpose(), axis=0)

        if not self.config.vlim:
            vmin = 0
            vmax = precip.max()

        else:
            vmin = self.config.vlim[0]
            vmax = self.config.vlim[1]

        region = [self.config.longitude[0], self.config.longitude[1], self.config.latitude[0], self.config.latitude[1]]

        # Add contour lines
        inline = True if self.config.isolines and self.config.isolines != 0 else False
        self.ax = self.add_isolines(region, self.config.isolines, inline=inline)

        im = self.ax.imshow(precip, vmin=vmin, vmax=vmax, extent=region, cmap=self.config.colorbar)
        self.ax.set_ylim(self.config.latitude[0], self.config.latitude[1])
        self.ax.set_xlim(self.config.longitude[0], self.config.longitude[1])

        # Add a color bar
        cbar = plt.colorbar(im, ax=self.ax)

        cbar.set_label(self.config.labels['ylabel'])
        self.ax.set_title(self.config.labels['title'])

        if self.config.volcano_name:
            self.ax.scatter(self.config.volcano_position[1], self.config.volcano_position[0], color='red', marker='^', s=50, label=self.config.volcano_name[0], zorder=3)
            self.ax.legend(fontsize='small', frameon=True, framealpha=0.3)

        if self.config.save:
            self.ax.savefig(self.config.save_path)

        if self.config.show_flag:
            plt.show()


    def add_isolines(self, region, levels=0, inline=False):
        grid = pygmt.datasets.load_earth_relief(resolution="01m", region=region)

        if not isinstance(levels, int):
            levels = int(levels[0])

        # Convert the DataArray to a numpy array
        grid_np = grid.values

        # Perform the operation
        grid_np[grid_np < 0] = 0

        # Convert the numpy array back to a DataArray
        grid[:] = grid_np

        # Plot the data
        cont = self.ax.contour(grid, levels=levels, colors='white', extent=region, linewidths=0.5)

        if levels !=0:
            self.ax.clabel(cont, inline=inline, fontsize=8)

        return self.ax


    def modify_dataframe(self, df):
        if  self.config.average in ['W', 'M', 'Y'] or  self.config.cumulate:
            df = weekly_monthly_yearly_precipitation(df,  self.config.average,  self.config.cumulate)

        if  self.config.interpolate:
            df = interpolate_map(df, self.config.interpolate)

        return df