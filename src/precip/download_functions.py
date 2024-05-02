import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import sys
import os
import re
import concurrent.futures
import threading
import subprocess
import time
import netCDF4 as nc
from precip.helper_functions import ask_user
from precip.config import json_download_url, final06, final07


def crontab_volcano_json(json_path, json_download_url=json_download_url):
    """
    Downloads a JSON file containing volcano eruption data from a specified URL and saves it to the given file path.

    Args:
        json_path (str): The file path where the JSON file will be saved.
        json_download_url (str): The URL from which the JSON file will be downloaded.

    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs while downloading the JSON file.

    Returns:
        None
    """
    # TODO add crontab to update json file every ???
    # TODO call the variable from the config file 
    json_download_url = json_download_url
    
    try:
        result = requests.get(json_download_url)
    
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            print(f'Error: {err.response.status_code} Url Not Found')
            sys.exit(1)

        else:
            print('An HTTP error occurred: ' + str(err.response.status_code))
            sys.exit(1)

    f = open(json_path, 'wb')
    f.write(result.content)
    f.close()

    if os.path.exists(json_path):
        print(f'Json file downloaded in {json_path}')

    else:
        print('Cannot create json file')


def generate_url_download(date, final06=final06, final07=final07):
    # Creates gpm_data folder if it doesn't exist
    intervals = {"Final06": datetime.strptime(final06, '%Y-%m-%d').date(),
                 "Final07": datetime.strptime(final07, '%Y-%m-%d').date(),
                 "Late06": datetime.today().date() - relativedelta(days=1)}
    
    # Final Run 06
    if date <= intervals["Final06"]:    
        head = 'https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.06/'
        body = '/3B-DAY.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V06.nc4'

    # Late Run 06
    elif date > intervals["Final07"]:
        head = 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.06/'
        body = '/3B-DAY-L.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V06.nc4'

    # Final Run 07
    else:
        head = 'https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/'
        body = '/3B-DAY.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V07B.nc4'

    year = str(date.year)
    day = str(date.strftime('%d'))
    month = str(date.strftime('%m'))

    url = head + year + '/' + month + body + year+month+day + tail

    return url


def generealte_urls_list(date_list):
    """
    Generate a list of URLs for downloading precipitation data.

    Parameters:
    date_list (list): A list of dates for which the precipitation data will be downloaded.

    Returns:
    list: A list of URLs for downloading precipitation data.

    """
    urls = []

    for date in date_list:
        url = generate_url_download(date)
        urls.append(url)

    return urls


def dload_site_list_parallel(folder, date_list):
    """
    Downloads files from a list of URLs in parallel using multiple threads.

    Args:
        folder (str): The folder path where the downloaded files will be saved.
        date_list (list): A list of dates or URLs to download.

    Returns:
        None
    """

    if not os.path.exists(folder):
        os.makedirs(folder)

    urls = generealte_urls_list(date_list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for url in urls:
            filename = os.path.basename(url)
            file_path = os.path.join(folder, filename)

            if not os.path.exists(file_path):
                print(f"Starting download of {url} on {threading.current_thread().name}")
                attempts = 0

                while attempts < 3:
                    try:
                        subprocess.run(['wget', url, '-P', folder], check=True)
                        print(f"Finished download of {url} on {threading.current_thread().name}")
                        break

                    except subprocess.CalledProcessError:
                        attempts += 1
                        print(f"Download attempt {attempts} failed for {url}. Retrying...")
                        time.sleep(1)
                        
                else:
                    print(f"Failed to download {url} after {attempts} attempts. Exiting...")
                    sys.exit(1)
            else:
                print(f"File {filename} already exists, skipping download")

    # if ask_user('check'):
    #     check_nc4_files(folder)    


def check_nc4_files(folder):
    # Get a list of all .nc4 files in the directory
    files = [folder + '/' + f for f in os.listdir(folder) if f.endswith('.nc4')]
    corrupted_files = []
    print('Checking for corrupted files...')

    # Check if each file exists and is not corrupted
    for file in files:
        try:
            # Try to open the file with netCDF4
            ds = nc.Dataset(file)
            ds.close()

        except:
            print(f"File is corrupted: {file}")
            # Delete the corrupted file
            os.remove(file)
            print(f"Corrupted file has been deleted: {file}")
            corrupted_files.append(file)

    if len(corrupted_files) > 0:
        print(f"Corrupted files found: {corrupted_files}")
        print(f"Total corrupted files: {len(corrupted_files)}")
        print('Retrying download of corrupted files...')
        date_list=[]

        for f in corrupted_files:
            d = re.search('\d{8}', f)
            date_list.append(datetime.strptime(d.group(0), "%Y%m%d").date())

        dload_site_list_parallel(folder, date_list)

    print('All files have been checked')