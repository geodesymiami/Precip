from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
from matplotlib import gridspec
from matplotlib.lines import Line2D
from scipy.interpolate import interp2d

import pygmt
import pandas as pd
import numpy as np

from precip.objects.classes.configuration import PlotConfiguration
from precip.objects.interfaces.plotter.plotter import Plotter
from precip.objects.interfaces.plotter.event_plotter import EventsPlotter

from precip.helper_functions import  weekly_monthly_yearly_precipitation, from_nested_to_float, map_eruption_colors, days_in_month
from precip.config import ELNINOS


class MapPlotter(Plotter):
    def __init__(self, fig, grid, config: PlotConfiguration):
        self.fig = fig
        self.ax = self.fig.add_subplot(grid)
        self.config = config


    def plot(self, data):
        data = self.modify_dataframe(data)

        if type(data) == pd.DataFrame:
            data = data.get('Precipitation')[0][0]

        elif type(data) == dict:
            data = data[self.config.date_list[0].strftime('%Y-%m-%d')]

        data = np.flip(data.transpose(), axis=0)

        if not self.config.vlim:
            vmin = 0
            vmax = data.max()

        else:
            vmin = self.config.vlim[0]
            vmax = self.config.vlim[1]

        region = [self.config.longitude[0], self.config.longitude[1], self.config.latitude[0], self.config.latitude[1]]

        # Add contour lines
        inline = True if self.config.isolines and self.config.isolines != 0 else False

        self.ax = self.add_isolines(region, self.config.isolines, self.config.iso_color,inline=inline)

        im = self.ax.imshow(data, vmin=vmin, vmax=vmax, extent=region, cmap=self.config.colorbar)
        self.ax.set_aspect('auto')
        self.ax.set_ylim(self.config.latitude[0], self.config.latitude[1])
        self.ax.set_xlim(self.config.longitude[0], self.config.longitude[1])

        # Add a color bar
        cbar = plt.colorbar(im, ax=self.ax)

        cbar.set_label(self.config.labels['ylabel'])
        self.ax.set_title(self.config.labels['title'])

        if self.config.volcano_name:
            self.ax.scatter(self.config.volcano_position[1], self.config.volcano_position[0], color='red', marker='^', s=50, label=self.config.volcano_name[0], zorder=3)
            self.ax.legend(fontsize='xx-small', frameon=True, framealpha=0.3)

        if self.config.save:
            self.fig.savefig(self.config.save_path)

        if self.config.show_flag:
            plt.show()
        else:
            plt.close(self.fig)
            return self.ax


    def add_isolines(self, region, levels=0, colors='white',inline=False):
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
        cont = self.ax.contour(grid, levels=levels, colors=colors, extent=region, linewidths=0.5)

        if levels !=0:
            self.ax.clabel(cont, inline=inline, fontsize=8)

        return self.ax


    def interpolate_map(self, dataframe):
        """
        Interpolates a precipitation map using scipy.interpolate.interp2d.

        Parameters:
        dataframe (pandas.DataFrame): The input dataframe containing the precipitation data.
        resolution (int): The resolution factor for the interpolated map. Default is 5.

        Returns:
        numpy.ndarray: The interpolated precipitation map.
        """

        try:
            values = dataframe.get('Precipitation')[0][0]

        except:
            values = dataframe[0]

        x = np.arange(values.shape[1])
        y = np.arange(values.shape[0])
        # Create the interpolator function
        interpolator = interp2d(x, y, values)

        # Define the new x and y values with double the resolution
        new_x = np.linspace(x.min(), x.max(), values.shape[1]*self.config.interpolate)
        new_y = np.linspace(y.min(), y.max(), values.shape[0]*self.config.interpolate)

        # Perform the interpolation
        new_values = interpolator(new_x, new_y)

        return new_values


    def modify_dataframe(self, data):
        df = weekly_monthly_yearly_precipitation(data,  self.config.average,  self.config.cumulate)

        if  self.config.interpolate:
            df = self.interpolate_map(data)

        return df


class BarPlotter(EventsPlotter):
    def __init__(self, fig, grid, config: PlotConfiguration):
        self.fig = fig
        self.ax = self.fig.add_subplot(grid)
        self.config = config


    def plot(self, data):
        data = self.modify_dataframe(data)

        if self.config.style == 'strength':
            width = 1.1
            x = range(len(data))

        else:
            width = 0.01
            x = data['Decimal']

        y = data['roll']

        self.ax.set_ylabel(self.config.labels['ylabel'])

        if self.config.log == True:
            self.ax.set_yscale('log')
            self.ax.set_yticks([0.1, 1, 10, 100, 1000])

        self.ax.set_title(self.config.labels['title'])

        self.ax.bar(x, y, color=data['color'], width=width, alpha=1)

        if not self.config.style == 'strength':
            self.ax.set_xlabel('Year')
            start = int(data['Decimal'].min() // 1)
            end = int(data['Decimal'].max() // 1 + 1)

            ticks = [start + (2*i) for i in range(((end - start) // 2) + 1)]
            labels = ["'" + str(start + (2*i))[-2:] for i in range(((end - start) // 2) + 1)]

            self.ax.set_xticks(ticks)
            self.ax.set_xticklabels(labels)
            plot2 = self.ax.twinx()
            plot2.bar(data['Decimal'], data['cumsum'], color ='gray', width = width, alpha = .05)

            y2_label = ("Cumulative\n"
                        "precipitation\n"
                        "(mm)")

            plot2.set_ylabel(y2_label, rotation=90, labelpad= 10)
            self.legend_handles += [mpatches.Patch(color='gray', label=self.config.labels['y2label'])]

        if self.config.elnino and not self.config.style == 'strength':
            self.plot_elninos(data)

        if 'Eruptions' in data and len(data[data['Eruptions'].notna()]) >= 1:
            self.plot_eruptions(data)

        self.ax.legend(handles=self.legend_handles, loc='upper left', fontsize='xx-small')
        # plt.tight_layout()

        if self.config.save:
            self.fig.savefig(self.config.save_path)

        if self.config.show_flag:
            plt.show()
        else:
            plt.close(self.fig)
            return self.ax


    def modify_dataframe(self, data):
            if self.config.bins > 1:
                self.legend_handles = [mpatches.Patch(color=self.config.colors[i], label=self.config.quantile + str(i+1)) for i in range(self.config.bins)]

            else:
                self.legend_handles = []

            if  self.config.average in ['W', 'M', 'Y'] or  self.config.cumulate:
                data = weekly_monthly_yearly_precipitation(data,  self.config.average,  self.config.cumulate)

            data = map_eruption_colors(data, self.config.roll, self.config.eruption_dates, self.config.bins, self.config.colors)

            if self.config.style == 'strength':
                # Sort the data by 'roll' column
                data = data.sort_values(by='roll')
                # Reset the index of the DataFrame
                data = data.reset_index(drop=True)

            data = from_nested_to_float(data)

            return data


    def plot_elninos(self, data):
        global ELNINOS

        cmap = plt.cm.bwr
        colors = {'strong nino': [cmap(253), 'Strong El Niño'], 'strong nina': [cmap(3), 'Strong La Niña']}

        end = data['Decimal'].max()
        ticks = int((data['roll'].max() * 1.5) // 1)
        linewidth = 21900 // len(data['Date'].unique())

        for j in ['strong nino', 'strong nina']:
            for x1, x2 in ELNINOS[j]:
                if x1 > end:
                    continue

                x2 = min(x2, end)

                self.ax.plot([x1, x2], [ticks - .125, ticks - .125], color=colors[j][0], alpha=1.0, linewidth=6)

                if colors[j][1] not in [i.get_label() for i in self.legend_handles]:
                    self.legend_handles.append(mpatches.Patch(color=colors[j][0], label=colors[j][1]))


    def plot_eruptions(self, data):
        if self.config.style == 'strength':
            eruptions = data[data['Eruptions'].notna()].index

        else:
            eruptions = data[data['Eruptions'].notna()]['Eruptions']

        for x in eruptions:
            self.ax.axvline(x=x, color='black', linestyle='dashed', dashes=(9,6), linewidth=1)

        self.legend_handles += [Line2D([0], [0], color='black', linestyle='dashed', dashes= (3,2), label='Volcanic event', linewidth= 1)]


class AnnualPlotter(EventsPlotter):
    def __init__(self, fig, grid, config: PlotConfiguration):
        self.fig = fig
        self.grid = grid
        self.config = config


    def plot(self, data):
        data = self.modify_dataframe(data)

        first_date = data['Decimal'].min()
        last_date = data['Decimal'].max()

        start = int(first_date // 1)
        end = int(last_date // 1 + 1)

        # Create a GridSpec for the subplot within the third slot of the main layout
        sub_gs = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=self.grid, width_ratios=[4, 1])

        # Create two sub-axes within the third slot of the main layout
        self.ax0 = self.fig.add_subplot(sub_gs[0])
        self.ax1 = self.fig.add_subplot(sub_gs[1])

        # TODO by_season
        # Plots rain by quantile, and if by_season is True, then also by year.
        if False:
            for i in range(color_count):
                if by_season == True:
                    for j in range(start, end + 1):
                        rain_by_year = volc_rain[volc_rain['Decimal'] // 1 == j].copy()
                        rain_j = rain_by_year.sort_values(by=['roll'])
                        dates_j = np.array([rain_j['Decimal']])
                        bin_size = len(dates_j) // color_count
                        x = dates_j % 1
                        y = dates_j // 1
                        self.ax0.scatter(x[i*bin_size:(i+1)*bin_size], y[i*bin_size:(i+1)*bin_size], color=colors[i], marker='s', s=(219000 // len(rainfall['Date'].unique())))

        x = data['Decimal'] % 1
        y = data['Decimal'] // 1
        self.ax0.scatter(x, y, color=data['color'], marker='s', s=(219000 // len(data['Date'].unique())))

        ################### SIDEPLOT OF CUMULATIVE PER YEAR ###################

        totals = []
        for year in range(start, end+1):
            totals.append(data['Precipitation'][data['Decimal'] // 1 == year].sum())

        self.ax1.barh(range(start, end+1), totals, height=.5, color='purple')

        ########################################################################

        # Set plot properties
        self.ax0.set_yticks([start + (2*k) for k in range(((end + 2 - start) // 2))], [str(start + (2*k)) for k in range(((end + 2 - start) // 2))])
        self.ax0.set_xticks([(1/24 + (1/12)*k) for k in range(12)], ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'])
        self.ax0.set_xlabel("Month")
        self.ax0.set_ylabel("Year")
        self.ax0.set_title(self.config.labels['title'])
        self.ax1.set_title('Total (mm)')
        self.ax1.set_yticks([start + (2*k) for k in range(((end + 1 - start) // 2))], [str(start + (2*k)) for k in range(((end + 1 - start) // 2))])

        if self.config.elnino:
            self.plot_elninos(data)

        if 'Eruptions' in data.columns and len(data[data['Eruptions'].notna()]) >= 1:
            self.plot_eruptions(data)

        if self.legend_handles:
            self.ax0.legend(handles=self.legend_handles, loc='upper right', fontsize='xx-small')
        # plt.tight_layout()

        if self.config.save:
            self.fig.savefig(self.config.save_path)

        if self.config.show_flag:
            plt.show()
        else:
            plt.close(self.fig)



    def modify_dataframe(self, data):
        if self.config.bins > 1:
            self.legend_handles = [mpatches.Patch(color=self.config.colors[i], label=self.config.quantile + str(i+1)) for i in range(self.config.bins)]

        else:
            self.legend_handles = []

        data = map_eruption_colors(data, self.config.roll, self.config.eruption_dates, self.config.bins, self.config.colors)

        data = from_nested_to_float(data)

        return data


    def plot_elninos(self, data):
        global ELNINOS

        cmap = plt.cm.bwr
        colors = {'strong nino': [cmap(253), 'Strong El Niño'], 'strong nina': [cmap(3), 'Strong La Niña']}

        end = data['Decimal'].max()
        linewidth = 20000 // len(data['Date'].unique())

        for j in ['strong nino', 'strong nina']:
            for x1, x2 in ELNINOS[j]:
                if x1 > end:
                    continue

                x2 = min(x2, end)

                y1, x1 = divmod(x1, 1)  # Split 2000.25 into 2000 and 0.25
                y2, x2 = divmod(x2, 1)

                # if y1 == y2:
                #     self.ax0.plot([x1, x2], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                # else:
                self.ax0.plot([x1, 1.001], [y1 - .25, y1 - .25], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                self.ax0.plot([-.0022, x2], [y2 - .25, y2 - .25], color=colors[j][0], alpha=1.0, linewidth=linewidth)

                if colors[j][1] not in [i.get_label() for i in self.legend_handles]:
                    self.legend_handles.append(mpatches.Patch(color=colors[j][0], label=colors[j][1]))


    def plot_eruptions(self, data):
        x = []
        for _, row in data.iterrows():
            if pd.notna(row['Eruptions']):
                x.append((row['Date'].month / 13) + (row['Date'].day / (days_in_month(row['Date']) * 10)))
            else:
                x.append(row['Eruptions'] % 1)        

        y = [(i // 1) + .5 for i in data['Eruptions']]  # Take the integer part of the date i.e. 2020

        eruption = self.ax0.scatter(x, y, color='black', marker='v', label='Volcanic Events')
        self.legend_handles.append(eruption)