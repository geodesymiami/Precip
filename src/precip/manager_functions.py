import os
from precip.helper_functions import generate_date_list, check_missing_dates, str_to_masked_array
from precip.volcano_functions import volcanoes_list
from precip.config import JSON_VOLCANO


def handle_data_functions(inps):
    from precip import JetStream
    from precip import CloudFileManager
    from precip import LocalFileManager


    if inps.download:
        date_list = generate_date_list(inps.start_date, inps.end_date, inps.average)

        if inps.use_ssh:
            jtstream = JetStream()
            CloudFileManager(jtstream).download(date_list)

        else:
            local = LocalFileManager(inps.dir)
            local.download(date_list)

    if inps.check:
        if inps.use_ssh:
            jtstream = JetStream()
            CloudFileManager(jtstream).check_files()

        else:
            local = LocalFileManager(inps.dir)
            local.check_files()

    # KA: this is a useful function but should be moved to the command line script
    if inps.list:
        volcanoes_list(os.path.join(inps.dir, JSON_VOLCANO))


def get_precipitation_data(inps):
    from precip import Database
    from precip import Queries

    if inps.use_ssh:
        from precip import JetStream
        from precip import CloudFileManager
        from precip import CloudSQLite3Database
        from precip import CloudSQLite3Operations

        #inps.latitude, inps.longitude, date_list, gpm_dir

        #Create and connect to JetStream
        jtstream = JetStream()
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

            #Get missing data from files
            data = NC4DataSource(CloudNC4Data(jtstream)).get_data(inps.latitude, inps.longitude, missing_dates)

            #Load data into the database
            Database(CloudSQLite3Operations(jetstream_database)).load_data(inps.latitude, inps.longitude, data)

            #Get data
            precipitation = Database(CloudSQLite3Operations(jetstream_database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Close the database
        jetstream_database.close()

    else:
        from precip import SQLite3Database
        from precip import SQLite3Operations

        #Create and connect to Database
        database = SQLite3Database()
        database.connect()

        #Check table
        SQLite3Operations(database).check_table()

        #Get data
        precipitation = Database(SQLite3Operations(database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Check missing dates
        missing_dates = check_missing_dates(inps.date_list, precipitation['Date'])

        if missing_dates:
            from precip import LocalNC4Data
            from precip import NC4DataSource

            #Get missing data from files
            data = NC4DataSource(LocalNC4Data(inps.gpm_dir)).get_data(inps.latitude, inps.longitude, missing_dates)

            #Load data into the database
            Database(SQLite3Operations(database)).load_data(inps.latitude, inps.longitude, data)

            #Get data
            precipitation = Database(SQLite3Operations(database)).get_data(Queries.extract_precipitation(inps.latitude, inps.longitude, inps.date_list))

        #Close the database
        database.close()

    precipitation['Precipitation'] = str_to_masked_array(precipitation['Precipitation'])

    return precipitation

# TODO add examples notebook
# TODO remove DS_STORE
# TODO move this directly into main
def handle_plotters(inps, main_gs=None, fig=None):
    # TODO move the import in the __init__.py of each folder
    from precip import PlotConfiguration
    from precip import MapPlotter, BarPlotter, AnnualPlotter
    from matplotlib import pyplot as plt

    input_config = PlotConfiguration(inps)
    # TODO add this method to the __init__
    input_config.configure_arguments(inps)
    precipitation = get_precipitation_data(input_config)

    # TODO this has to be added to the 'all' script
    # main_gs = gridspec.GridSpec(1, 1, figure=fig)

    if main_gs is None:
        fig = plt.figure(constrained_layout=True)
        main_gs = 111

    if inps.style == 'map':
        graph = MapPlotter(fig, main_gs, input_config)

    if inps.style in ['daily', 'weekly', 'monthly','bar', 'strength']:
        graph = BarPlotter(fig, main_gs, input_config)

    if inps.style == 'annual':
        graph = AnnualPlotter(fig, main_gs, input_config)

    graph.plot(precipitation)

    return fig