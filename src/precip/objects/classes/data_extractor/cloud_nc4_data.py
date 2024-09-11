from precip.objects.interfaces.data_managers.abstract_data_from_file import AbstractDataFromFile
from precip.objects.interfaces.abstract_cloud_manager import AbstractCloudManager
from precip.config import PATH_JETSTREAM
import re
import os
import netCDF4 as nc
import numpy as np
import tempfile
from datetime import datetime


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
