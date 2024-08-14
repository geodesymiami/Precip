from precip.objects.interfaces.database.abstract_database_operations import AbstractDatabaseOperations
from precip.objects.interfaces.database.abstract_cloud_database_connection import AbstractCloudDatabaseConnection
from precip.objects.classes.Queries.queries import Queries



class CloudSQLite3Operations(AbstractDatabaseOperations):
    def __init__(self, database: AbstractCloudDatabaseConnection) -> None:
        self.database = database


    def select_data(self, query: str):
        self.database.cursor.execute(query)
        return self.database.cursor.fetchall()


    def check_table(self, table: str = 'volcanoes'):
        self.database.cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (table,))

        if not self.database.cursor.fetchone():
            self.database.cursor.execute(Queries.create_table(table))
            self.database.connection.commit()

        print('Table checked')


    def insert_data(self, latitude: str, longitude: str, date: str, precipitation: str):
        self.database.cursor.execute(Queries.insert_precipitation(latitude, longitude, date, precipitation))
        self.database.connection.commit()