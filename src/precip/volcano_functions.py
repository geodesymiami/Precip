import os
import json
from datetime import datetime
import pandas as pd
from precip.download_functions import download_volcano_json
from precip.config import JSON_DOWNLOAD_URL, START_DATE, END_DATE
import requests


VOLCANO_FILE = os.environ.get('PRECIP_HOME') + '/src/precip/Holocene_Volcanoes_precip_cfg.xlsx'

# TODO to replace elninos with the following API #
# TODO eventually move to helper_functions.py
if False:
    # CHECK THIS FIRST https://psl.noaa.gov/enso/mei/
    req = requests.get('https://psl.noaa.gov/enso/mei/data/meiv2.data')
    print(req.text)

###################################################


def get_volcano_json(jsonfile, url):
    """
    Retrieves volcano data from a JSON file or a remote URL.

    Args:
        jsonfile (str): The path to the local JSON file.
        url (str): The URL to retrieve the JSON data from.

    Returns:
        dict: The JSON data containing volcano information.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as err:
        print("Error: ", err)
        print("Loading from local file\n")

        if not os.path.exists(jsonfile):
            print(f'Error: {jsonfile} does not exist. Downloading...\n')
            download_volcano_json(jsonfile, JSON_DOWNLOAD_URL)

        f = open(jsonfile)
        data = json.load(f)

    return data


def volcanoes_list(jsonfile):
    """
    Retrieves a list of volcano names from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.

    Returns:
        None
    """
    data = get_volcano_json(jsonfile, JSON_DOWNLOAD_URL)

    volcanoName = []
    volcanoId = []
    volcanoCoordinates = []

    for j in data['features']:
        if j['properties']['VolcanoNumber'] not in volcanoId:
            volcanoName.append(j['properties']['VolcanoName'])
            volcanoId.append(j['properties']['VolcanoNumber'])
            volcanoCoordinates.append(j['geometry']['coordinates'])


    for volcano, id, coord in zip(volcanoName, volcanoId, volcanoCoordinates):
        print(f'{volcano}, id: {id}, coordinates: {coord[0]}, {coord[1]}')

    return volcanoName


def extract_volcanoes_info(jsonfile, volcanoId, vei=1, strength=False):
    """
    Extracts information about a specific volcano from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.
        volcanoName (str): The name of the volcano to extract information for.

    Returns:
        tuple: A tuple containing the start dates of eruptions, a date list, and the coordinates of the volcano.
    """
    column_names = ['Volcano', 'Start', 'End', 'Max Explosivity']

    data = get_volcano_json(jsonfile, JSON_DOWNLOAD_URL)

    start_dates = []
    frame_data = []
    name = ''

    first_day = datetime.strptime(START_DATE, '%Y%m%d').date()
    last_day = datetime.strptime(END_DATE, '%Y%m%d').date()

    try:
        volcanoId = int(volcanoId)
    except ValueError:
        id = []
        coords = []
        # Iterate over the features in the data
        for j in data['features']:
            if j['properties']['VolcanoName'] == volcanoId:
                if j['properties']['VolcanoNumber'] not in id:
                    id.append(j['properties']['VolcanoNumber'])
                    coords.append(j['geometry']['coordinates'])

        if len(id) > 1:
            print(f'Multiple volcanoes found with name: {volcanoId}')
            print('Please select one of the following volcano ids:')
            for id, coord in zip(id, coords):
                print(f'id: {id}, coordinates: {coord[0]}, {coord[1]}')
            exit()
        else:
            volcanoId = id[0]

    # Iterate over the features in the data
    for j in data['features']:
        if j['properties']['VolcanoNumber'] == volcanoId:
            if j['properties']['ExplosivityIndexMax'] < vei:
                continue

            name = (j['properties']['VolcanoName'])
            start = datetime.strptime((j['properties']['StartDate']), '%Y%m%d').date()

            coordinates = j['geometry']['coordinates']
            coordinates = coordinates[::-1]
            try:
                end = datetime.strptime((j['properties']['EndDate']), '%Y%m%d').date()

            except:
                end = 'None'

            print(f'{name} (id: {volcanoId}) eruption started {start} and ended {end}')

            # If the start date is within the date range
            if start >= first_day and start <= last_day:
                start_dates.append(start)

            if strength:
                stren = j['properties']['ExplosivityIndexMax']
                frame_data.append([name, start, end, stren])

    if name == '':
        volc_dict = get_volcanoes()
        coordinates = [volc_dict[volcanoId]['latitude'], volc_dict[volcanoId]['longitude']]
        name = volc_dict[volcanoId]['name']

    if strength:
    # If no start dates were found within the date range
        df = pd.DataFrame(frame_data, columns=column_names)
        return df

    # else:
    #     if not start_dates:
    #         # Print an error message and exit the program
    #         msg = f'Error: {volcanoName} eruption date is out of range'
    #         raise ValueError(msg)

    if start_dates != []:

        start_dates = sorted(start_dates)

        print('-'*50)
        print('Sorting eruptions by date...')
        print('-'*50)
        for d in start_dates:
            print('Extracted eruption in date: ', d)

        print('-'*50)

    print('')

    return start_dates, coordinates, name


def get_volcanoes():
    """
    Retrieves volcano data from an Excel file and returns a dictionary of volcano information.

    Returns:
        dict: A dictionary containing volcano information, with volcano names as keys and a dictionary of volcano attributes as values.
            The volcano attributes include 'id', 'latitude', and 'longitude'.
    """
    df = pd.read_excel(VOLCANO_FILE, skiprows=1)
    df = df[df['Precip'] != False]

    volcano_dict = {
        r['Volcano Number']: {
            'name': r['Volcano Name'],
            'latitude': r['Latitude'],
            'longitude': r['Longitude']
        } for _, r in df.iterrows()}

    return volcano_dict