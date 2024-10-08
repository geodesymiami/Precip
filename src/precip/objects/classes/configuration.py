import os
from precip.config import JSON_VOLCANO
from precip.helper_functions import generate_date_list, adapt_coordinates, color_scheme, quantile_name
from precip.volcano_functions import extract_volcanoes_info

# copy inps to self object
# for key, value in inps.__dict__.items():
#     setattr(self, key, value)

class PlotConfiguration:
    def __init__(self, inps):
        # copy inps to self object
        for key, value in inps.__dict__.items():
            setattr(self, key, value)

        self.configure_arguments(inps)


    def configure_arguments(self, inps):
        self.gpm_dir = inps.dir
        self.volcano_json_dir = os.path.join(inps.dir, JSON_VOLCANO)
        self.date_list =  generate_date_list(inps.start_date, inps.end_date, inps.average)
        self.eruption_dates = []

        if len(self.date_list) <= self.roll and not inps.style == 'map':
            msg = 'Error: The number of dates is less than the rolling window.'
            raise ValueError(msg)

        if inps.latitude and inps.longitude:
            self.latitude, self.longitude = adapt_coordinates(inps.latitude, inps.longitude)

        elif inps.volcano_name:
            self.eruption_dates, lalo, self.id = extract_volcanoes_info(self.volcano_json_dir, inps.volcano_name[0])
            self.latitude, self.longitude = adapt_coordinates(lalo[0], lalo[1])

            if inps.style == 'map':
                self.roll = 1
                self.volcano_position = [self.latitude[0], self.longitude[0]]

                self.latitude = [round(min(self.latitude) - 2, 2), round(max(self.latitude) + 2, 2)]
                self.longitude = [round(min(self.longitude) - 2, 2), round(max(self.longitude) + 2, 2)]

            else:
                if inps.add_event:
                    self.eruption_dates.extend(inps.add_event if isinstance(inps.add_event, list) else list(inps.add_event))

                if inps.bins:
                    self.colors = color_scheme(self.bins)
                    self.quantile = quantile_name(self.bins)

        self.plot_labels()

        if inps.save:
            self.save_config()


    def plot_labels(self):
        if self.style in ['daily', 'bar', 'strength']:
            ylabel = (
                f"{str(self.roll)} day\n"
                "precipitation\n"
                "(mm)"
            )

        elif self.style == 'map':
            if self.cumulate:
                ylabel = (
                    f"Cumulative precipitation\n"
                    f"over {len(self.date_list)} days\n"
                    "(mm)"
                )
            else:
                ylabel = (
                    f"Daily precipitation\n"
                    f"over {len(self.date_list)} days\n"
                    "(mm/day)"
                )

        else:
            ylabel = (
                f"{self.style}\n"
                "precipitation (mm)"
            )

        if self.volcano_name:
            title = f'{self.volcano_name[0]} - Latitude: {self.latitude}, Longitude: {self.longitude}'

        else:
            title = f'Latitude: {self.latitude}, Longitude: {self.longitude}'

        self.labels = {'title': title,
        'ylabel': ylabel,
        'y2label': 'Cumulative precipitation'}


    def save_config(self):
        if self.volcano_name:
                if self.save == 'volcano-name':
                    save_name = self.volcano_name[0]

                elif self.save == 'volcano-id':
                    save_name = self.id

        elif self.latitude and self.longitude:
            save_name = f'{self.latitude}_{self.longitude}'

        strStart = str(self.start_date).replace('-', '') if not isinstance(self.start_date, str) else self.start_date.replace('-', '')
        strEnd = str(self.end_date).replace('-', '') if not isinstance(self.end_date, str) else self.end_date.replace('-', '')
        self.save_path = f'{self.outdir}/{save_name}_{strStart}_{strEnd}_{self.style}_{self.bins}.png'