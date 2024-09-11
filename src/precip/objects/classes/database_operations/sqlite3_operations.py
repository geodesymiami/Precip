from interfaces import AbstractDatabaseOperations
from interfaces import AbstractDatabaseConnection
from classes import Queries


class SQLite3Operations(AbstractDatabaseOperations):
    def __init__(self, database: AbstractDatabaseConnection) -> None:
        self.database = database


    def select_data(self, query: str):
        self.database.cursor.execute(query)
        return self.database.cursor.fetchall()


    def check_table(self, table: str = 'volcanoes'):
        self.database.cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', (table,))

        if not self.database.cursor.fetchone():
            self.database.cursor.execute(f"""
            CREATE TABLE {table} (
                Date TEXT,
                Precipitation TEXT,
                Latitude REAL,
                Longitude REAL
            )
        """)
            self.database.connection.commit()

        print('Table checked')


    def insert_data(self, latitude: str, longitude: str, date: str, precipitation: str):
        self.database.cursor.execute(Queries.insert_precipitation(latitude, longitude, date, precipitation))
        self.database.connection.commit()


    def record_exists(self, latitude: str, longitude: str, date: str):
        self.database.cursor.execute(Queries.select_row(latitude, longitude, date))
        return self.database.cursor.fetchone() is not None