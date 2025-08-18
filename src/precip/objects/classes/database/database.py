from precip.objects.interfaces.data_managers.abstract_dataloader import AbstractDataLoader
from precip.objects.interfaces.database.abstract_database_operations import AbstractDatabaseOperations
from tqdm import tqdm
import pandas as pd
import json



class Database(AbstractDataLoader):
    def __init__(self, operator: AbstractDatabaseOperations) -> None:
        self.operator = operator


    def get_data(self, query: str):
        print('-' * 50)
        print('Extracting Values from Database ...\n')

        data = self.operator.select_data(query)

        columns = [column[0] for column in self.operator.database.cursor.description]
        df = pd.DataFrame.from_records(data=data, columns=columns)
        return df


    def load_data(self, latitude: str, longitude: str, dataframe: pd.DataFrame):
        # Convert the 'Precipitation' column to a string
        dataframe['Precipitation'] = dataframe['Precipitation'].apply(lambda x: json.dumps(x.tolist()))

        print('-' * 50)
        print('Inserting Values in Database ...\n')

        # Wrap the iterrows() loop with tqdm
        for index, row in tqdm(dataframe.iterrows(), total=len(dataframe), desc="Inserting data", unit="row"):
            self.operator.insert_data(latitude, longitude, row['Date'], row['Precipitation'], row['Version'])

        print('Values Inserted in Database\n')


    def remove_data(self, query: str):
        self.operator.remove_duplicates(query)