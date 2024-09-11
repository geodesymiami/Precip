from interfaces import AbstractDatabaseConnection
import sqlite3
import os
from precip.config import DATABASE


class SQLite3Database(AbstractDatabaseConnection):
    def __init__(self, path: str = os.getenv('PRECIP_DIR'), database_name: str = DATABASE):
        self.db_full_path = os.path.join(path, database_name)
        self.connection = None


    def connect(self):
        self.connection = sqlite3.connect(self.db_full_path)
        self.cursor = self.connection.cursor()
        print(f"Connected to the database")


    def close(self):
        if self.connection:
            self.connection.close()

        print(f"Connection to the database closed")