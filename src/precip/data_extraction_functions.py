from precip.helper_functions import check_missing_dates, str_to_masked_array
from precip.objects.classes.credentials_settings.credentials import PrecipVMCredentials
from precip.cli.download_precipitation import download_precipitation

# TODO for profiling
import time
from datetime import datetime


def get_precipitation_data(inps):
    from precip.objects.classes.database.database import Database
    from precip.objects.classes.Queries.queries import Queries

    if inps.use_ssh:
        from precip.objects.classes.providers.jetstream import JetStream
        from precip.objects.classes.file_manager.cloud_file_manager import CloudFileManager
        from precip.objects.classes.database.cloud_sqlite3_database import CloudSQLite3Database
        from precip.objects.classes.database_operations.cloud_sqlite3_operations import CloudSQLite3Operations

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

        # Get data
        precipitation = Database(CloudSQLite3Operations(jetstream_database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Check missing dates
        missing_dates = check_missing_dates(inps.date_list, precipitation['Date'])

        if missing_dates:
            from precip.objects.classes.data_extractor.cloud_nc4_data import CloudNC4Data
            from precip.objects.classes.data_extractor.nc4_datasource import NC4DataSource

            try:
                #Get missing data from files
                data = NC4DataSource(CloudNC4Data(jtstream)).get_data(inps.latitude, inps.longitude, missing_dates)

            except ValueError as e:
                print(e.args[0])
                missing_files = e.args[1]  # Dates to be downloaded
                download_precipitation(inps.use_ssh, missing_files, inps.gpm_dir)

                # Retry to get the data
                data = NC4DataSource(CloudNC4Data(jtstream)).get_data(inps.latitude, inps.longitude, missing_dates)

            #Load data into the database
            Database(CloudSQLite3Operations(jetstream_database)).load_data(inps.latitude, inps.longitude, data)

            #Get data
            precipitation = Database(CloudSQLite3Operations(jetstream_database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Close the database
        jetstream_database.close()

    else:
        from precip.objects.classes.database.sqlite3_database import SQLite3Database
        from precip.objects.classes.database_operations.sqlite3_operations import SQLite3Operations

        #Create and connect to Database
        database = SQLite3Database()
        database.connect()

        #Check table
        SQLite3Operations(database).check_table()

        # TODO for profiling
        start_time = time.time()
        print('Start db extraction at:', datetime.fromtimestamp(start_time))

        #Get data
        precipitation = Database(SQLite3Operations(database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        # TODO apply to ssh case too
        ################# Make as function ###################

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

        print()
        print("Elapsed time database extraction: ", time.time() - start_time, "seconds")
        print()

        #Check missing dates
        missing_dates = check_missing_dates(inps.date_list, precipitation['Date'])

        if missing_dates:
            from precip.objects.classes.data_extractor.local_nc4_data import LocalNC4Data
            from precip.objects.classes.data_extractor.nc4_datasource import NC4DataSource

            try:
                # TODO for profiling
                start_time = time.time()
                print('Start file extraction at:', datetime.fromtimestamp(start_time))

                #Get missing data from files
                data = NC4DataSource(LocalNC4Data(inps.gpm_dir)).get_data(inps.latitude, inps.longitude, missing_dates)

                print()
                print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
                print()

            except ValueError as e:
                print(e.args[0])
                missing_files = e.args[1]  # Dates to be downloaded
                download_precipitation(inps.use_ssh, missing_files, inps.gpm_dir)

                # TODO for profiling
                start_time = time.time()
                print('Start file extraction at:', datetime.fromtimestamp(start_time))

                # Retry to get the data
                data = NC4DataSource(LocalNC4Data(inps.gpm_dir)).get_data(inps.latitude, inps.longitude, missing_dates)

                # TODO for profiling
                print()
                print("Elapsed time file extracion: ", time.time() - start_time, "seconds")
                print()

            # TODO for profiling
            start_time = time.time()
            print('Start db upload at:', datetime.fromtimestamp(start_time))

            #Load data into the database
            Database(SQLite3Operations(database)).load_data(inps.latitude, inps.longitude, data)

            # TODO for profiling
            print()
            print("Elapsed time file upload: ", time.time() - start_time, "seconds")
            print()

            #Get data
            precipitation = Database(SQLite3Operations(database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Close the database
        database.close()

    precipitation['Precipitation'] = str_to_masked_array(precipitation['Precipitation'])

    return precipitation