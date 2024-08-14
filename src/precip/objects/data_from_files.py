from abc import ABC, abstractmethod
from databases import AbstractDataSource
from classes.file_utils import ReadNC4Properties
from databases import AbstractCloudFileManager
from classes.file_manager.cloud_file_manager import AbstractCloudManager
from classes.providers.jetstream import JetStream
from precip.helper_functions import generate_coordinate_array
import os
import netCDF4 as nc
import numpy as np
import pandas as pd
from precip.config import PATH_JETSTREAM
import tempfile
import re
from datetime import datetime


class AbstractFileHandler(ABC):
    @abstractmethod
    def check_duplicates(self):
        pass


    @abstractmethod
    def list_files(self):
        pass


class AbstractDataFromFile(AbstractFileHandler):
    @abstractmethod
    def process_file(self):
        pass


class LocalNC4Data(AbstractDataFromFile):
    def __init__(self, folder) -> None:
        self.path = folder


    def check_duplicates(self):
        print(f"Checking for duplicate files in {self.folder} ...")

        if len(self.files) != len(set(self.files)):
            print("There are duplicate files in the list.")

        else:
            print("There are no duplicate files in the list.")


    def process_file(self, file, date_list, lon, lat, longitude, latitude):
        date = ReadNC4Properties(file).get_date('date')

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


class CloudNC4Data(AbstractDataFromFile):
    def __init__(self, provider: AbstractCloudManager) -> None:
        self.provider = provider
        self.path = self.provider.path


    def check_duplicates(self):
        print(f"Checking for duplicate files in {self.path} ...")

        if len(self.files) != len(set(self.files)):
            print("There are duplicate files in the list.")

        else:
            print("There are no duplicate files in the list.")


    def process_file(self, file, date_list, lon, lat, longitude, latitude):
        d = re.search('\d{8}', file)
        date = datetime.strptime(d.group(0), "%Y%m%d").date()

        if date not in date_list:
            return None

        with tempfile.NamedTemporaryFile(suffix='.nc4', delete=True) as tmp:
            # Download the file to your local system
            self.provider.sftp.get(file, tmp.name)

            # Open the NetCDF file
            ds = nc.Dataset(tmp.name)
            data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']
            subset = data[:,
                        np.where(lon == longitude[0])[0][0]:np.where(lon == longitude[1])[0][0]+1,
                        np.where(lat == latitude[0])[0][0]:np.where(lat == latitude[1])[0][0]+1]
            subset = subset.astype(float)

        return (str(date), subset)


    def list_files(self, path: str = PATH_JETSTREAM):
        stdin, stdout, stderr = self.provider.ssh.exec_command(f"ls {path}")

        # Wait for the command to finish executing
        stdout.channel.recv_exit_status()

        all_files = stdout.read().decode()

        # Get a list of all .nc4 files in the directory
        self.files = [f for f in (os.path.join(path, file) for file in all_files.split('\n')) if f.endswith('.nc4')]


class NC4DataSource(AbstractDataSource):
    def __init__(self, data_extracted = AbstractDataFromFile) -> None:
        self.data_extracted = data_extracted


    def get_data(self, latitude, longitude, date_list):
        lon, lat = generate_coordinate_array()
        self.data_extracted.list_files(self.data_extracted.path)
        self.data_extracted.check_duplicates()

        finaldf = pd.DataFrame()
        results = []

        for file in self.data_extracted.files:
            result = self.data_extracted.process_file(file, date_list, lon, lat, longitude, latitude)

            if result is not None:
                results.append(result)

        df1 = pd.DataFrame(results, columns=['Date', 'Precipitation'])
        finaldf = pd.concat([finaldf, df1], ignore_index=True, sort=False)

        finaldf = finaldf.sort_values(by='Date', ascending=True).reset_index(drop=True)

        return finaldf




# TEST
from precip.helper_functions import generate_date_list
date_list = generate_date_list('20000601', '20000605')
latitude = [-7.55,-7.55]
longitude = [110.45,110.45]

if False:
    folder = os.path.join(os.getenv('SCRATCHDIR'), 'gpm_data')
    dd = NC4DataSource(LocalNC4Data(folder)).get_data(latitude, longitude, date_list)
    print(dd)


if True:
    jtstrm = JetStream()
    jtstrm.connect()
    jtstrm.open_sftp()
    dd = NC4DataSource(CloudNC4Data(jtstrm)).get_data(latitude, longitude, date_list)
    print(dd)
    jtstrm.close()