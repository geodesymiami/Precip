from precip.objects.classes.Queries.queries import Queries
from precip.objects.classes.database.database import Database
from precip.objects.classes.providers.jetstream import JetStream
from precip.objects.classes.database.sqlite3_database import SQLite3Database
from precip.objects.classes.data_extractor.local_nc4_data import LocalNC4Data
from precip.objects.classes.data_extractor.cloud_nc4_data import CloudNC4Data
from precip.objects.classes.data_extractor.nc4_datasource import NC4DataSource
from precip.objects.classes.file_manager.cloud_file_manager import CloudFileManager
from precip.objects.classes.credentials_settings.credentials import PrecipVMCredentials
from precip.objects.classes.database.cloud_sqlite3_database import CloudSQLite3Database
from precip.objects.classes.database_operations.sqlite3_operations import SQLite3Operations
from precip.objects.classes.database_operations.cloud_sqlite3_operations import CloudSQLite3Operations
from precip.cli.download_precipitation import download_precipitation
from precip.helper_functions import check_missing_dates, str_to_masked_array
from precip.config import RELIABLE_VERSION

# TODO for profiling
import time
from datetime import datetime

def remove_duplicates(precipitation, database, inps):
    """
    Removes duplicate entries from the precipitation DataFrame and the SQLite database.

    Args:
        precipitation (pd.DataFrame): The DataFrame containing precipitation data.
        database (str): The path to the SQLite database.
        inps (object): An object containing latitude and longitude attributes.

    Returns:
        pd.DataFrame: The updated DataFrame with duplicates removed.
    """
    # Identify duplicates
    duplicates = precipitation[precipitation['Date'].duplicated(keep=False)]

    # Remove duplicates from DataFrame
    precipitation = precipitation[~precipitation['Date'].isin(duplicates['Date'])]

    if not duplicates.empty:
        # Remove duplicates from SQLite database
        print('Removing duplicates from Database ...')
        # TODO remove data with invalid values
        for date in duplicates['Date']:
            if inps.use_ssh:
                op = CloudSQLite3Operations(database)
            else:
                op = SQLite3Operations(database)

            Database(op).remove_data(Queries.remove_records(inps.latitude, inps.longitude, date))

        print('Duplicates Removed from Database')

    return precipitation

def setup_database(inps):
    """
    Sets up the database connection and data source based on the input parameters.

    Parameters:
    inps (object): An object containing input parameters, including:
        - use_ssh (bool): Indicates whether to use SSH for connection.
        - gpm_dir (str): Directory for local GPM data if SSH is not used.

    Returns:
    tuple: A tuple containing:
        - database: The database connection object.
        - db_ops: The database operations object.
        - nc4_source: The data source for NC4 data.
    """
    if inps.use_ssh:
        jtstream = JetStream(PrecipVMCredentials())
        jtstream.connect()
        jtstream.open_sftp()
        file_manager = CloudFileManager(jtstream)
        database = CloudSQLite3Database(file_manager)
        database.connect()
        db_ops = CloudSQLite3Operations(database)
        nc4_source = NC4DataSource(CloudNC4Data(jtstream))
    else:
        database = SQLite3Database()
        database.connect()
        db_ops = SQLite3Operations(database)
        nc4_source = NC4DataSource(LocalNC4Data(inps.gpm_dir))
    return database, db_ops, nc4_source


def extract_precipitation_data(db_ops, nc4_source, database, inps):
    db = Database(db_ops)
    db_ops.check_table()

    start_time = time.time()
    print("-" * 50)
    print(f"Start db extraction at: {datetime.fromtimestamp(start_time)}\n")

    precipitation = db.get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

    print(f"Elapsed time database extraction: {time.time() - start_time}\n")
    print("-" * 50)

    remove_duplicates(precipitation, database, inps)

    missing_dates = check_missing_dates(inps.date_list, precipitation['Date'])

    if not missing_dates:
        return precipitation

    try:
        print("Start file extraction at:", datetime.fromtimestamp(time.time()))
        data = nc4_source.get_data(inps.latitude, inps.longitude, missing_dates)
    except ValueError as e:
        print(e.args[0])
        missing_files = e.args[1]
        download_precipitation(inps.use_ssh, missing_files, inps.gpm_dir)
        data = nc4_source.get_data(inps.latitude, inps.longitude, missing_dates)

    db.load_data(inps.latitude, inps.longitude, data)

    results = db.get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))
    results = results.sort_values(by=['Date', 'Version'], ascending=[True, False])
    to_drop = results[(results['Date'].duplicated(keep='first')) & (results['Version'] != RELIABLE_VERSION)].index

    results = results.drop(to_drop)

    return results


def get_precipitation_data(inps):
    database, db_ops, nc4_source = setup_database(inps)
    precipitation = extract_precipitation_data(db_ops, nc4_source, database, inps)
    database.close()

    precipitation['Precipitation'] = str_to_masked_array(precipitation['Precipitation'])

    return precipitation

################## REFACTORED CODE END ########################


############################## OLD ######################################

def get_precipitation_data_old(inps):
    if inps.use_ssh:
        #inps.latitude, inps.longitude, date_list, gpm_dir

        #Create and connect to JetStream
        jtstream = JetStream(PrecipVMCredentials())
        jtstream.connect()
        jtstream.open_sftp()

        #Create CloudFileManager object
        jetstream_filemanager = CloudFileManager(jtstream)

        #Create CloudSQLite3Database object
        jetstream_database = CloudSQLite3Database(jetstream_filemanager)

        #Connect to the database
        jetstream_database.connect()

        # Check table
        CloudSQLite3Operations(jetstream_database).check_table()

        start_time = time.time()
        print('Start db extraction at:', datetime.fromtimestamp(start_time))

        # Get data
        precipitation = Database(CloudSQLite3Operations(jetstream_database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        remove_duplicates(precipitation, database, inps)

        print("-"* 50)
        print("Elapsed time database extraction: ", time.time() - start_time, "seconds")
        print("-"* 50)

        #Check missing dates
        missing_dates = check_missing_dates(inps.date_list, precipitation['Date'])

        if missing_dates:
            from precip.objects.classes.data_extractor.cloud_nc4_data import CloudNC4Data
            from precip.objects.classes.data_extractor.nc4_datasource import NC4DataSource

            try:
                start_time = time.time()
                print("-"* 50)
                print('Start file extraction at:', datetime.fromtimestamp(start_time))
                print("-"* 50)

                #Get missing data from files
                data = NC4DataSource(CloudNC4Data(jtstream)).get_data(inps.latitude, inps.longitude, missing_dates)

                print("-"* 50)
                print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
                print("-"* 50)

            except ValueError as e:
                print(e.args[0])
                missing_files = e.args[1]  # Dates to be downloaded
                download_precipitation(inps.use_ssh, missing_files, inps.gpm_dir)

                start_time = time.time()
                print("-"* 50)
                print('Start file extraction at:', datetime.fromtimestamp(start_time))
                print("-"* 50)

                # Retry to get the data
                data = NC4DataSource(CloudNC4Data(jtstream)).get_data(inps.latitude, inps.longitude, missing_dates)

                print("-"* 50)
                print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
                print("-"* 50)

            start_time = time.time()
            print("-"* 50)
            print('Start file extraction at:', datetime.fromtimestamp(start_time))
            print("-"* 50)

            #Load data into the database
            Database(CloudSQLite3Operations(jetstream_database)).load_data(inps.latitude, inps.longitude, data)

            print("-"* 50)
            print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
            print("-"* 50)

            #Get data
            precipitation = Database(CloudSQLite3Operations(jetstream_database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Close the database
        jetstream_database.close()

    else:
        #Create and connect to Database
        database = SQLite3Database()
        database.connect()

        #Check table
        SQLite3Operations(database).check_table()

        # TODO for profiling
        start_time = time.time()
        print("-"* 50)
        print('Start db extraction at:', datetime.fromtimestamp(start_time))
        print("-"* 50)

        #Get data
        precipitation = Database(SQLite3Operations(database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        # TODO apply to ssh case too
        ################# Make as function ###################

        remove_duplicates(precipitation, database, inps)

        if False:
            # Identify duplicates
            duplicates = precipitation[precipitation['Date'].duplicated(keep=False)]

            # Remove duplicates from DataFrame
            precipitation = precipitation[~precipitation['Date'].isin(duplicates['Date'])]

            if not duplicates.empty:
                # Remove duplicates from SQLite database
                print('Removing duplicates from Database ...')
                # TODO remove data with invalid values
                for date in duplicates['Date']:
                    Database(SQLite3Operations(database)).remove_data(Queries.remove_records(inps.latitude, inps.longitude, date))

                print('Duplicates Removed from Database')

        # precipitation['Precipitation'].isfloat

        ######################################################

        print("-"* 50)
        print("Elapsed time database extraction: ", time.time() - start_time, "seconds")
        print("-"* 50)

        #Check missing dates
        missing_dates = check_missing_dates(inps.date_list, precipitation['Date'])

        if missing_dates:
            from precip.objects.classes.data_extractor.local_nc4_data import LocalNC4Data
            from precip.objects.classes.data_extractor.nc4_datasource import NC4DataSource

            try:
                # TODO for profiling
                start_time = time.time()
                print("-"* 50)
                print('Start file extraction at:', datetime.fromtimestamp(start_time))
                print("-"* 50)

                #Get missing data from files
                data = NC4DataSource(LocalNC4Data(inps.gpm_dir)).get_data(inps.latitude, inps.longitude, missing_dates)

                print("-"* 50)
                print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
                print("-"* 50)

            except ValueError as e:
                print(e.args[0])
                missing_files = e.args[1]  # Dates to be downloaded
                download_precipitation(inps.use_ssh, missing_files, inps.gpm_dir)

                # TODO for profiling
                start_time = time.time()
                print("-"* 50)
                print('Start file extraction at:', datetime.fromtimestamp(start_time))
                print("-"* 50)

                # Retry to get the data
                data = NC4DataSource(LocalNC4Data(inps.gpm_dir)).get_data(inps.latitude, inps.longitude, missing_dates)

                # TODO for profiling
                print("-"* 50)
                print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
                print("-"* 50)

            # TODO for profiling
            start_time = time.time()
            print("-"* 50)
            print('Start file extraction at:', datetime.fromtimestamp(start_time))
            print("-"* 50)

            #Load data into the database
            Database(SQLite3Operations(database)).load_data(inps.latitude, inps.longitude, data)

            # TODO for profiling
            print("-"* 50)
            print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
            print("-"* 50)

            #Get data
            precipitation = Database(SQLite3Operations(database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Close the database
        database.close()

    precipitation['Precipitation'] = str_to_masked_array(precipitation['Precipitation'])

    return precipitation