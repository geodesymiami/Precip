import netCDF4
from datetime import datetime
from precip.objects.interfaces.file_utils import AbstractFileUtils


class ReadNC4Properties(AbstractFileUtils):
    def __init__(self, path: str,):
        self.path = path


    def get_date(self, type: str = 'string'):
        with netCDF4.Dataset(self.path) as dataset:
            date = dataset.getncattr('BeginDate')

            if type == 'string':
                date = date.replace('-', '')
                return date

            elif type == 'date':
                return datetime.strptime(date, '%Y-%m-%d').date()


    def get_attributes(self):
        print("Global attributes:")

        with netCDF4.Dataset(self.path) as dataset:
            for attr in dataset.ncattrs():
                print(f"{attr}: {dataset.getncattr(attr)}")