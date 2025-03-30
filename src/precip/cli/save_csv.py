import os
from precip.config import JSON_VOLCANO
from precip.helper_functions import generate_date_list, adapt_coordinates
from precip.volcano_functions import extract_volcanoes_info
import argparse
from datetime import datetime
from precip.data_extraction_functions import get_precipitation_data
from precip.helper_functions import create_eruption_csv
from precip.utils.argument_parsers import add_date_arguments, add_location_arguments, add_save_arguments


PRECIP_DIR = os.getenv('PRECIP_DIR')

EXAMPLE = f"""
Example:

Save precipitation data over a volcano specifing the period and output directory:
save_csv.py --id 353060 --period 20200101:20201231 --outdir /path/to/output/directory

Add an event manually to the time series, save to current directory:
save_csv.py --id 353060 --add-event 20170310

Select the minimum volcanic explosivity index:
save_csv.py --id 353060 --vei 2
"""

def create_parser(iargs=None, namespace=None):
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('--id',
                        nargs='?',
                        type=float,
                        default=None,
                        help='Volcano name')
    parser.add_argument("--vei",
                        nargs="?",
                        type=int,
                        default=1,
                        help="Minimum volcanic explosivity index")
    parser.add_argument('--add-event',
                        nargs='*',
                        metavar=('YYYYMMDD, YYYY-MM-DD'),
                        help='Add event to the time series')
    parser.add_argument('--use-ssh',
                        action='store_true',
                        dest='use_ssh',
                        help='Use ssh')

    parser = add_date_arguments(parser)
    parser = add_save_arguments(parser)
    parser = add_location_arguments(parser)

    inps = parser.parse_args(iargs, namespace)

    inps.dir = PRECIP_DIR
    inps.gpm_dir = inps.dir


    if not inps.period:
        inps.start_date = datetime.strptime(inps.start_date, '%Y%m%d').date()

        #End date subject to variations, check for alternatives on config.py
        inps.end_date = datetime.strptime(inps.end_date, '%Y%m%d').date()

    else:
        if ':' in inps.period:
            dates = inps.period.split(':')
        # TODO not sure if this is to be removed
        elif ',' in inps.period:
            dates = inps.period.split(',')

        inps.start_date = datetime.strptime(dates[0], '%Y%m%d').date()
        inps.end_date = datetime.strptime(dates[1], '%Y%m%d').date()

    if not inps.polygon:
        if inps.latitude:
            if len(inps.latitude) == 1:
                inps.latitude = parse_coordinates(inps.latitude[0])

            elif len(inps.latitude) == 2:
                inps.latitude = [float(inps.latitude[0]), float(inps.latitude[1])]

            else:
                parser.error("--latitude requires 1 or 2 arguments")

        if inps.longitude:
            if len(inps.longitude) == 1:
                inps.longitude = parse_coordinates(inps.longitude[0])

            elif len(inps.longitude) == 2:
                inps.longitude = [float(inps.longitude[0]), float(inps.longitude[1])]

            else:
                parser.error("--longitude requires 1 or 2 arguments")

        if inps.lalo:
            coordinates = parse_coordinates(inps.lalo)
            inps.latitude = parse_coordinates(coordinates[0])
            inps.longitude = parse_coordinates(coordinates[1])
            inps.latitude, inps.longitude = [min(inps.latitude), max(inps.latitude)], [min(inps.longitude), max(inps.longitude)]


    else:
        inps.latitude, inps.longitude = parse_polygon(inps.polygon)

    inps.date_list =  generate_date_list(inps.start_date, inps.end_date)

    return inps


def parse_polygon(polygon):
    """
    Parses a polygon string retreive from ASF vertex tool and extracts the latitude and longitude coordinates.

    Args:
        polygon (str): The polygon string in the format "POLYGON((lon1 lat1, lon2 lat2, ...))".

    Returns:
        tuple: A tuple containing the latitude and longitude coordinates as lists.
               The latitude list contains the minimum and maximum latitude values.
               The longitude list contains the minimum and maximum longitude values.
    """
    latitude = []
    longitude = []
    pol = polygon.replace("POLYGON((", "").replace("))", "")

    # Split the string into a list of coordinates
    for word in pol.split(','):
        if (float(word.split(' ')[1])) not in latitude:
            latitude.append(float(word.split(' ')[1]))
        if (float(word.split(' ')[0])) not in longitude:
            longitude.append(float(word.split(' ')[0]))

    longitude = [round(min(longitude),2), round(max(longitude),2)]
    latitude = [round(min(latitude),2), round(max(latitude),2)]

    return latitude, longitude


def parse_coordinates(coordinates):
    """
    Parse the given coordinates string and convert it into a list of floats.

    Args:
        coordinates (str): The coordinates string to be parsed.

    Returns:
        list: A list of floats representing the parsed coordinates.

    Raises:
        ValueError: If the coordinates string is invalid.

    """
    if isinstance(coordinates, str):
        coordinates = coordinates.replace("'", '').replace('"', '')

        try:
            if ',' in coordinates:
                coordinates = coordinates.split(',')

            elif ':' in coordinates:
                coordinates = coordinates.split(':')
                coordinates = [float(i) for i in coordinates]

            elif ' ' in coordinates:
                coordinates = coordinates.split(' ')
                coordinates = [float(i) for i in coordinates]

            else:
                coordinates = [float(coordinates), float(coordinates)]

        except ValueError:
            msg=f'Error: {coordinates} invalid coordinate/s'
            raise ValueError(msg)

        return coordinates

    else:
        coordinates = [coordinates, coordinates]

        return coordinates


def main(iargs=None, namespace=None):
    # TODO finish pls
    inps = create_parser(iargs, namespace)

    os.makedirs(PRECIP_DIR, exist_ok=True)
    if inps.id:
        volcano_json_dir = os.path.join(inps.dir, JSON_VOLCANO)
        eruption_dates, lalo, name = extract_volcanoes_info(volcano_json_dir, inps.id, inps.vei)
        inps.latitude, inps.longitude = adapt_coordinates(lalo[0], lalo[1])
        if inps.add_event:
            eruption_dates.extend(inps.add_event if isinstance(inps.add_event, list) else list(inps.add_event))

    inps.latitude, inps.longitude = adapt_coordinates(inps.latitude, inps.longitude)

    precipitation = get_precipitation_data(inps)

    if name:
        name = name.replace(',', '').replace(' ', '')
    else:
        name = inps.latitude, inps.longitude
    file = os.path.join(inps.outdir, f'{name}_{inps.start_date}_{inps.end_date}.csv')
    create_eruption_csv(file, precipitation, eruption_dates)


if __name__ == "__main__":
    main()