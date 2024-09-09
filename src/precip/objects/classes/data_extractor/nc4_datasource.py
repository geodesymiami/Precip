from precip.objects.interfaces.data_managers.abstract_datasource import AbstractDataSource
from precip.objects.interfaces.data_managers.abstract_data_from_file import AbstractDataFromFile
from precip.helper_functions import generate_coordinate_array
import pandas as pd


class NC4DataSource(AbstractDataSource):
    def __init__(self, data_extracted = AbstractDataFromFile) -> None:
        self.data_extracted = data_extracted


    def get_data(self, latitude, longitude, date_list):
        lon, lat = generate_coordinate_array()
        self.data_extracted.list_files()
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