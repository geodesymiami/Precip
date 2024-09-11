from interfaces import AbstractDataLoader
from interfaces import AbstractDatabaseOperations
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
            if not self.operator.record_exists(latitude, longitude, row['Date']):
                self.operator.insert_data(latitude, longitude, row['Date'], row['Precipitation'])

        print('Values Inserted in Database')
