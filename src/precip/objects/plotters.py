from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
import pygmt
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from precip.objects.configuration import Configuration
from precip.plotter_functions import interpolate_map
from precip.helper_functions import volcano_rain_frame, color_scheme, quantile_name, weekly_monthly_yearly_precipitation, adapt_events, date_to_decimal_year, from_nested_to_float
from precip.config import ELNINOS

class Plotter(ABC):
    @abstractmethod
    def plot(self):
        pass


class MapPlotter(Plotter):
    def __init__(self, ax, config: Configuration):
        self.ax = ax
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
        self.ax = self.add_isolines(region, self.config.isolines, inline=inline)

        im = self.ax.imshow(data, vmin=vmin, vmax=vmax, extent=region, cmap=self.config.colorbar)
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


    def modify_dataframe(self, data):
        if  self.config.average in ['W', 'M', 'Y'] or  self.config.cumulate:
            df = weekly_monthly_yearly_precipitation(data,  self.config.average,  self.config.cumulate)

        if  self.config.interpolate:
            df = interpolate_map(data, self.config.interpolate)

        return df


class BarPlotter(Plotter):
    def __init__(self, ax, config: Configuration):
        self.ax = ax
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

            plot2.set_ylabel("Cumulative precipitation (mm)", rotation=270, labelpad= 10)
            self.legend_handles += [mpatches.Patch(color='gray', label=self.config.labels['y2label'])]

        if self.config.elnino and not self.config.style == 'strength':
            self.plot_elninos(data)

        if self.config.add_event or self.config.eruption_dates != []:
            self.plot_eruptions(data)

        self.ax.legend(handles=self.legend_handles, loc='upper left', fontsize='small')
        plt.tight_layout()

        if self.config.save:
            self.ax.savefig(self.config.save_path)

        if self.config.show_flag:
            plt.show()


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
                # TODO This is for annual
                if self.ax and False:
                    y1, x1 = divmod(x1, 1)  # Split 2000.25 into 2000 and 0.25
                    y2, x2 = divmod(x2, 1)

                    if y1 == y2:
                        self.ax.plot([x1, x2], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                    else:
                        self.ax.plot([x1, 1.0022], [y1 - .17, y1 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                        self.ax.plot([-.0022, x2], [y2 - .17, y2 - .17], color=colors[j][0], alpha=1.0, linewidth=linewidth)
                else:
                    self.ax.plot([x1, x2], [ticks - .125, ticks - .125], color=colors[j][0], alpha=1.0, linewidth=6)

                if colors[j][1] not in [i.get_label() for i in self.legend_handles]:
                    self.legend_handles.append(mpatches.Patch(color=colors[j][0], label=colors[j][1]))


    def plot_eruptions(self, data):
        from matplotlib.lines import Line2D
        # TODO This is for annual
        # if self.ax:
        #     x = [i % 1 for i in data['Eruptions']]  # Take the decimal part of the date i.e. 0.25
        #     y = [(i // 1) + .5 for i in data['Eruptions']]  # Take the integer part of the date i.e. 2020
        #     scatter_size = 219000 // len(data['Date'].unique())
        #     eruption = self.ax.scatter(x, y, color='black', marker='v', s=scatter_size, label='Volcanic Events')
        #     self.legend_handles.append(eruption)

        if self.config.style == 'strength':
            eruptions = data[data['Eruptions'].notna()].index

        else:
            eruptions = data[data['Eruptions'].notna()]['Eruptions']

        for x in eruptions:
            self.ax.axvline(x=x, color='black', linestyle='dashed', dashes=(9,6), linewidth=1)

        self.legend_handles += [Line2D([0], [0], color='black', linestyle='dashed', dashes= (3,2), label='Volcanic event', linewidth= 1)]


    def modify_dataframe(self, data):
        colors = color_scheme(self.config.bins)
        quantile = quantile_name(self.config.bins)

        if self.config.bins > 1:
            self.legend_handles = [mpatches.Patch(color=colors[i], label=quantile + str(i+1)) for i in range(self.config.bins)]

        else:
            self.legend_handles = []

        if  self.config.average in ['W', 'M', 'Y'] or  self.config.cumulate:
            data = weekly_monthly_yearly_precipitation(data,  self.config.average,  self.config.cumulate)

        data = volcano_rain_frame(data, self.config.roll)

        if self.config.eruption_dates != []:
            # Adapt the eruption dates to the averaged precipitation data
            self.config.eruption_dates = adapt_events(self.config.eruption_dates, data['Date'])

            # Create a dictionary where the keys are the eruption dates and the values are the same
            eruption_dict = {date: date for date in self.config.eruption_dates}

            # Map the 'Date' column to the eruption dates
            data['Eruptions'] = data['Date'].map(eruption_dict)

            # Convert to decimal year for plotting purposes
            data['Eruptions'] = data.Eruptions.apply(date_to_decimal_year)

        # Calculate 'color' based on ranks of the 'roll' column
        data['color'] = ((data['roll'].rank(method='first') * self.config.bins) / len(data)).astype(int).clip(upper=self.config.bins-1)

        # Map the 'color' column to the `colors` list
        data['color'] = data['color'].map(lambda x: colors[x])

        if self.config.style == 'strength':

            # Sort the data by 'roll' column
            data = data.sort_values(by='roll')
            # Reset the index of the DataFrame
            data = data.reset_index(drop=True)

        data = from_nested_to_float(data)

        return data
    


class AnnualPlotter(Plotter):
    def __init__(self, ax, config: Configuration):
        self.ax = ax
        self.config = config