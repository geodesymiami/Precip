import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import concurrent.futures
import threading
import subprocess
import time
from precip.helper_functions import ask_user
from precip.config import JSON_DOWNLOAD_URL, FINAL06, FINAL07, PATH_JETSTREAM


def download_volcano_json(json_path, json_download_url=JSON_DOWNLOAD_URL):
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
    try:
        result = requests.get(json_download_url)

        with open(json_path, 'wb') as f:
            f.write(result.content)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            msg = f'Error: {err.response.status_code} Url Not Found'
            raise ValueError(msg)

        else:
            msg = 'An HTTP error occurred: ' + str(err.response.status_code)
            raise ValueError(msg)


    if os.path.exists(json_path):
        print(f'Json file downloaded in {json_path}')

    else:
        print('Cannot create json file')


def generate_url_download(date, final06=FINAL06, final07=FINAL07):
    """
    Generates the URL for downloading precipitation data based on the given date.

    Args:
        date (datetime.date): The date for which the precipitation data is needed.
        final06 (str): The date in the format 'YYYY-MM-DD' for the Final06 interval.
        final07 (str): The date in the format 'YYYY-MM-DD' for the Final07 interval.

    Returns:
        str: The URL for downloading the precipitation data.

    Raises:
        None
    """
    # Creates gpm_data folder if it doesn't exist
    intervals = {"Final06": datetime.strptime(final06, '%Y-%m-%d').date(),
                 "Final07": datetime.strptime(final07, '%Y-%m-%d').date(),
                 "Late06": datetime.today().date() - relativedelta(days=1)}
    # For research purpose is better to use Final run data, possibly v07
    # No Final run 06 anymore available on GES DISC
    # Final Run 07
    if date <= intervals["Final07"]:
        head = 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/'
        body = '/3B-DAY.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V07B.nc4'

    # Late Run 07
    elif date > intervals["Final07"]:
        head = 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.07/'
        body = '/3B-DAY-L.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V07B.nc4'

    # Late Run 07
    # else:
    #     head = 'https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/'
    #     body = '/3B-DAY.MS.MRG.3IMERG.'
    #     tail = '-S000000-E235959.V07B.nc4'

    year = str(date.year)
    day = str(date.strftime('%d'))
    month = str(date.strftime('%m'))

    url = head + year + '/' + month + body + year+month+day + tail

    return url


def generate_urls_list(date_list):
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


def dload_site_list_parallel(folder, date_list, parallel=5):
    """
    Downloads files from a list of URLs in parallel using multiple threads.

    Args:
        folder (str): The folder path where the downloaded files will be saved.
        date_list (list): A list of dates or URLs to download.

    Returns:
        None
    """

    os.makedirs(folder, exist_ok=True)

    urls = generate_urls_list(date_list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
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
                    msg = f"Failed to download {url} after {attempts} attempts. Exiting..."
                    raise ValueError(msg)
            else:
                print(f"\rFile {filename} already exists, skipping download. ", end="")
                time.sleep(0.001)

    print('')
    print('All files have been downloaded')
    print('-----------------------------------------------')


def download_jetstream(ssh, url, pathJetstream):
    filename = os.path.basename(url)
    file_path = os.path.join(pathJetstream, filename)

    # Check if the file already exists on the server
    stdin, stdout, stderr = ssh.exec_command(f'ls {file_path}')

    # Wait for the command to finish
    stdout.channel.recv_exit_status()

    if stdout.read().decode():
        print(f"\rFile {filename} already exists, skipping download. ", end="")
        return

    print(f"Starting download of {url} ")
    attempts = 0

    while attempts < 3:
        try:
            stdin, stdout, stderr = ssh.exec_command(f'wget -O {file_path} {url}')
            exit_status = stdout.channel.recv_exit_status()  # Wait for the command to finish

            if exit_status == 0:
                print(f"Finished download of {url} ")
            else:
                raise Exception(stderr.read().decode())

            break

        except Exception as e:
            attempts += 1
            print(f"Download attempt {attempts} failed for {url}. Retrying... Error: {str(e)}")
            time.sleep(1)

    else:
        msg = f"Failed to download {url} after {attempts} attempts. Exiting..."
        raise ValueError(msg)


# TODO Can be removed
def download_jetstream_parallel(date_list, ssh, parallel=5):
    # Generate the URLs
    urls = generate_urls_list(date_list)

    # Use a ThreadPoolExecutor to download the files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(download_jetstream, ssh, url, PATH_JETSTREAM) for url in urls]

    # Close the SSH client
    ssh.close()