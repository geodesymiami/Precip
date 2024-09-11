from interfaces import AbstractFileManager
from precip.download_functions import generate_urls_list
import concurrent.futures
import time
import os
import re
import netCDF4 as nc
from datetime import datetime
import threading
import subprocess


class LocalFileManager(AbstractFileManager):
    def __init__(self, folder: str):
        self.folder = folder


    def download(self, date_list: list, parallel: int = 5):
        os.makedirs(self.folder, exist_ok=True)
        urls = generate_urls_list(date_list)

        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            for url in urls:
                filename = os.path.basename(url)
                file_path = os.path.join(self.folder, filename)

                if not os.path.exists(file_path):
                    print(f"Starting download of {url} on {threading.current_thread().name}")
                    attempts = 0

                    while attempts < 3:
                        try:
                            subprocess.run(['wget', url, '-P', self.folder], check=True)
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


    def check_files(self):
        # Get a list of all .nc4 files in the directory
        files = [self.folder + '/' + f for f in os.listdir(self.folder) if f.endswith('.nc4')]
        corrupted_files = []
        print('Checking for corrupted files...')
        for file in files:
            try:
                # Try to open the file with netCDF4
                print(f"\rChecking file: {file}", end="")
                ds = nc.Dataset(file)
                ds.close()

            except:
                print(f"File is corrupted: {file}")
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

            self.download(self.folder, date_list, self.parallel)
