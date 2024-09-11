from interfaces import AbstractCloudManager
from interfaces import AbstractCloudFileManager
from precip.download_functions import generate_urls_list
import concurrent.futures
import tempfile
import time
import os
import re
import netCDF4 as nc
from datetime import datetime

class CloudFileManager(AbstractCloudFileManager):
    def __init__(self, provider: AbstractCloudManager) -> None:
        self.provider = provider


    def download(self, date_list: list, parallel: int = 5):
        # Connect
        self.provider.connect()

        # Generate the URLs
        urls = generate_urls_list(date_list)

        # Use a ThreadPoolExecutor to download the files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = [executor.submit(self.cloud_download, url) for url in urls]

        # Close the SSH client
        self.provider.close()


    def check_files(self):
        # Connect
        self.provider.connect()

        stdin, stdout, stderr = self.provider.ssh.exec_command(f'ls {self.provider.path}/*.nc4')
        files = stdout.read().decode().splitlines()
        client = self.provider.ssh.open_sftp()
        corrupted_files = []
        print('Checking for corrupted files...')
        for file in files:
            try:
                # Try to open the file with netCDF4
                print(f"\rChecking file: {file}", end="")

                with tempfile.NamedTemporaryFile(suffix='.nc4', delete=True) as tmp:

                    # Download the file to your local system
                    client.get(file, tmp.name)

                    # Open the NetCDF file
                    ds = nc.Dataset(tmp.name)
                    ds.close()

            except:
                print(f"File is corrupted: {file}")
                client.remove(file)
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

            self.download(date_list)

        else:
            print('')
            print('No corrupted files found')

        print('All files have been checked')
        print('-----------------------------------------------')

        # Close the SSH client
        self.provider.close()


    def cloud_download(self, url):
        ssh = self.provider.ssh
        pathJetstream = self.provider.path
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


    def create_temp_file(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=True)
