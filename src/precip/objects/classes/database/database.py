from precip.objects.interfaces.data_managers.abstract_dataloader import AbstractDataLoader
from precip.objects.interfaces.database.abstract_database_operations import AbstractDatabaseOperations
import pandas as pd
import json



class Database(AbstractDataLoader):
    def __init__(self, operator: AbstractDatabaseOperations) -> None:
        self.operator = operator


    def get_data(self, query: str):
        data = self.operator.select_data(query)

        columns = [column[0] for column in self.operator.database.cursor.description]
        df = pd.DataFrame.from_records(data=data, columns=columns)
        return df


    def load_data(self, latitude: str, longitude: str, dataframe: pd.DataFrame):
        # Convert the 'Precipitation' column to a string
        dataframe['Precipitation'] = dataframe['Precipitation'].apply(lambda x: json.dumps(x.tolist()))

        for index, row in dataframe.iterrows():
            self.operator.insert_data(latitude, longitude, row['Date'], row['Precipitation'])
        print('Values Inserted in Database')
