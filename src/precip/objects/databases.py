from abc import ABC, abstractmethod
import os
from precip.config import DATABASE, PATH_JETSTREAM
import sqlite3
import pandas as pd
from precip.objects.interfaces.file_manager.abstract_cloud_file_manager import AbstractCloudFileManager
from precip.objects.classes.Queries.queries import Queries



class AbstractDataSource(ABC):
    @abstractmethod
    def get_data(self):
        pass


class AbstractDatabaseConnection(ABC):
    @abstractmethod
    def connect(self):
        pass


    @abstractmethod
    def close(self):
        pass


class AbstractCloudDatabaseConnection(AbstractDatabaseConnection):
    def check_db(self):
        pass


    def create_db(self):
        pass


class AbstractDatabaseOperations(ABC):
    @abstractmethod
    def select_data(self):
        pass


    @abstractmethod
    def check_table(self):
        pass


    @abstractmethod
    def load_data(self):
        pass


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


    def load_data(self, date: str, precipitation: str, latitude: str, longitude: str,table: str = 'volcanoes'):
        self.database.cursor.execute(f"INSERT INTO {table} (Date, Precipitation, Latitude, Longitude) VALUES (?, ?, ?, ?)",
                    (date, precipitation, latitude, longitude))

        self.database.connection.commit()
        print('Values Inserted in Database')


class CloudSQLite3Database(AbstractCloudDatabaseConnection):
    def __init__(self, file_manager: AbstractCloudFileManager, path: str = PATH_JETSTREAM, database_name: str = DATABASE) -> None:
        self.file_manager = file_manager
        self.provider = file_manager.provider
        self.db_full_path = os.path.join(path, database_name)
        self.connection = None


    def connect(self):
        # Connect to the provider server through ssh
        self.provider.connect()

        # Open SFTP connection with Provider server
        self.provider.open_sftp()

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


class CloudSQLite3Operations(AbstractDatabaseOperations):
    def __init__(self, database: AbstractCloudDatabaseConnection) -> None:
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


    def load_data(self, date: str, precipitation: str, latitude: str, longitude: str,table: str = 'volcanoes'):
        self.database.cursor.execute(f"INSERT INTO {table} (Date, Precipitation, Latitude, Longitude) VALUES (?, ?, ?, ?)",
                    (date, precipitation, latitude, longitude))

        self.database.connection.commit()
        print('Values Inserted in Database')


class Database(AbstractDataSource):
    def __init__(self, operator: AbstractDatabaseOperations) -> None:
        self.operator = operator


    def get_data(self, query: str):
        data = self.operator.select_data(query)
        columns = [column[0] for column in self.operator.database.cursor.description]
        df = pd.DataFrame.from_records(data=data, columns=columns)
        return df



def check_missing_dates(date_list, column):
    column = pd.to_datetime(column).dt.date

    # Check if all dates in the date_list are in the DataFrame
    missing_dates = [date for date in date_list if date not in column.tolist()]

    if missing_dates:
        missing_dates.sort()

        date_list = generate_date_list(start=missing_dates[0], end=missing_dates[-1])
        precipitation = extract_precipitation(latitude, longitude, date_list, folder, ssh)

        precipitation['Precipitation'] = precipitation['Precipitation'].apply(lambda x: json.dumps(x.tolist()))

        # Insert the new rows into the 'volcanoes' table
        for index, row in precipitation.iterrows():
            cursor.execute("INSERT INTO volcanoes (Date, Precipitation, Latitude, Longitude) VALUES (?, ?, ?, ?)",
                        (row['Date'], row['Precipitation'], lat, lon))

        conn.commit()

        df = pd.read_sql_query(query, conn)


# TEST
from precip.helper_functions import generate_date_list
date_list = generate_date_list('20000601', '20000605')
latitude = '-7.55:-7.55'
longitude = '110.45:110.45'

if True:
    db = SQLite3Database()
    db.connect()
    SQLite3Operations(db).check_table()
    df = Database(SQLite3Operations(db)).get_data(Queries.extract_precipitation(latitude, longitude, date_list))
    print(df)
    db.close()


if False:
    from precip.objects.classes.providers.jetstream import JetStream
    from precip.objects.classes.file_manager.cloud_file_manager import CloudFileManager
    jtstream = JetStream()
    jtstrm_db = CloudSQLite3Database(CloudFileManager(jtstream))
    # Connect to database
    jtstrm_db.connect()
    # Check table
    CloudSQLite3Operations(jtstrm_db).check_table()
    # Get data
    df = Database(CloudSQLite3Operations(jtstrm_db)).get_data(Queries.extract_precipitation(latitude, longitude, date_list))
    jtstrm_db.close()
