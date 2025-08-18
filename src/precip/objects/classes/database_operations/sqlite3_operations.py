from precip.objects.interfaces.database.abstract_database_operations import AbstractDatabaseOperations
from precip.objects.interfaces.database.abstract_database_connection import AbstractDatabaseConnection
from precip.objects.classes.Queries.queries import Queries
from sqlite3 import IntegrityError


class SQLite3Operations(AbstractDatabaseOperations):
    def __init__(self, database: AbstractDatabaseConnection) -> None:
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


    def insert_data(self, latitude: str, longitude: str, date: str, precipitation: str, version: int):
        try:
            self.database.cursor.execute(Queries.insert_ignore_precipitation(latitude, longitude, date, precipitation, version))
            self.database.connection.commit()

        except IntegrityError:
            pass  # Record already exists, so we ignore this error


    def record_exists(self, latitude: str, longitude: str, date: str):
        self.database.cursor.execute(Queries.select_row(latitude, longitude, date))
        return self.database.cursor.fetchone() is not None


    def remove_duplicates(self, query: str):
        self.database.cursor.execute(query)
        self.database.connection.commit()