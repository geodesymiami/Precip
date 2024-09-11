from precip.objects.interfaces.database.abstract_cloud_database_connection import AbstractCloudDatabaseConnection
from precip.objects.interfaces.file_manager.abstract_cloud_file_manager import AbstractCloudFileManager
import sqlite3
import os
from precip.config import DATABASE, PATH_JETSTREAM



class CloudSQLite3Database(AbstractCloudDatabaseConnection):
    def __init__(self, file_manager: AbstractCloudFileManager, path: str = PATH_JETSTREAM, database_name: str = DATABASE) -> None:
        self.file_manager = file_manager
        self.provider = file_manager.provider
        self.db_full_path = os.path.join(path, database_name)
        self.connection = None


    def connect(self):
        # Create temporary file
        self.file_manager.create_temp_file()

        # Check if the database exists, if not, create
        try:
            self.check_db()

        except IOError:
            self.create_db()

        # Connect to the database
        self.connection = sqlite3.connect(self.db_temp_path)
        self.cursor = self.connection.cursor()
        print(f"Connected to the database")


    def close(self):
        with self.provider.sftp.file(self.db_full_path, 'wb') as f:
            with open(self.db_temp_path, 'rb') as local_file:
                f.write(local_file.read())
                print(f"Database saved on Provider server")

        self.file_manager.temp_file.close()
        self.connection.close()
        self.provider.close()


    def check_db(self):
        # Try to open the database file
        with self.provider.sftp.file(self.db_full_path, 'rb') as f:

            chunk_size = 1024 * 1024  # 1MB

            while True:
                chunk = f.read(chunk_size)

                if not chunk:
                    break

                self.file_manager.temp_file.write(chunk)

        self.db_temp_path = self.file_manager.temp_file.name
        print(f"Database found at {self.db_full_path}")


    def create_db(self):
        # Create Database
        with self.provider.sftp.file(self.db_full_path, 'wb') as f:
            pass

        self.db_temp_path = self.file_manager.temp_file.name
        print(f"Database created at {self.db_full_path}")
