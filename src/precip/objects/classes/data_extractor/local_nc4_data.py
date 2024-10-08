from precip.objects.interfaces.data_managers.abstract_data_from_file import AbstractDataFromFile
from precip.objects.classes.utils.file_utils import ReadNC4Properties
import os
import netCDF4 as nc
import numpy as np
import re
from datetime import datetime


class LocalNC4Data(AbstractDataFromFile):
    def __init__(self, folder) -> None:
        self.path = folder


    def check_duplicates(self):
        print(f"Checking for duplicate files in {self.path} ...")

        if len(self.files) != len(set(self.files)):
            print("There are duplicate files in the list.")

        else:
            print("There are no duplicate files in the list.")


    def process_file(self, file, date_list, lon, lat, longitude, latitude):
        #SLOWER
        if False:
            date = ReadNC4Properties(file).get_date('date')
        #FASTER
        d = re.search('\d{8}', file)
        date = datetime.strptime(d.group(0), "%Y%m%d").date()

        if date not in date_list:
            return None

        with nc.Dataset(file) as ds:
            data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']
        # If you want to work more than one location
        # results = []
        # for longitude, latitude in zip(longitude_pairs, latitude_pairs):
        # where inputs = longitude_pairs = [(10, 20), (30, 40), (50, 60)] and latitude_pairs = [(10, 20), (30, 40), (50, 60)]
            subset = data[:,
                        np.where(lon == longitude[0])[0][0]:np.where(lon == longitude[1])[0][0]+1,
                        np.where(lat == latitude[0])[0][0]:np.where(lat == latitude[1])[0][0]+1]
            subset = subset.astype(float)

        return (str(date), subset)


    def list_files(self):
        self.files = [self.path + '/' + f for f in os.listdir(self.path) if f.endswith('.nc4')]
