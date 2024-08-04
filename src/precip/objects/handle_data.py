from abc import ABC, abstractmethod
import os
import re
import time
import tempfile
import paramiko
import threading
import subprocess
import concurrent
import netCDF4 as nc
from datetime import datetime
from precip.download_functions import generealte_urls_list
from precip.config import PATH_JETSTREAM


class FileMethods(ABC):
    @abstractmethod
    def download(self, date_list, parallel=5):
        pass

    @abstractmethod
    def check_files(self):
        pass


class ConnectionMethods(ABC):
    @abstractmethod
    def connect(self):
        pass


    @abstractmethod
    def check_connected(self):
        pass


    @abstractmethod
    def close(self):
        pass


class JetStream(ConnectionMethods):
    def __init__(self, hostname: str = '149.165.154.65', username: str = 'exouser', rsa_key: str = '.ssh/id_rsa', path: str = PATH_JETSTREAM) -> None:
        self.path = path
        self.hostname = hostname
        self.username = username
        self.ssh = None

        # TODO Tailored to my(disilvestro) environment
        self.path_id_rsa = os.path.join(os.getenv('HOME'), rsa_key)
        self.ssh_key = self.path_id_rsa + '_jetstream' if os.path.exists(self.path_id_rsa + '_jetstream') else self.path_id_rsa


    def connect(self) -> None:
        for i in range(3):
            try:
                # Connect to the server
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.ssh_key)
                self.ssh = ssh
                print('Connected to the server')
                break

            except paramiko.SSHException as e:
                print(f"Attempt {i+1} failed to connect to the server: {e}")
                # Limit reached
                if i > 2:
                    self.ssh = None


    def check_connected(self) -> bool:
        return self.ssh and self.ssh.get_transport() and self.ssh.get_transport().is_active()


    def close(self) -> None:
        self.ssh.close()
        print('Connection closed')


class CloudFileManager(FileMethods):
    def __init__(self, provider: ConnectionMethods) -> None:
        self.provider = provider


    def download(self, date_list: list, parallel: int = 5):
        # Connect
        self.provider.connect()

        # Generate the URLs
        urls = generealte_urls_list(date_list)

        # Download the files
        self.download_files(urls, parallel)

        # Close the SSH client
        self.provider.close()


    def download_files(self, urls, parallel):
        # Use a ThreadPoolExecutor to download the files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = [executor.submit(self.download_jetstream, url) for url in urls]

    # Download the file
    def download_jetstream(self, url):
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

                self.download(date_list, self.provider.ssh, self.provider.parallel)

        else:
            print('')
            print('No corrupted files found')

        print('All files have been checked')
        print('-----------------------------------------------')

        # Close the SSH client
        self.provider.close()


class LocalFileManager(FileMethods):
    def __init__(self, folder: str):
        self.folder = folder


    def download(self, date_list: list, parallel: int = 5):
        os.makedirs(self.folder, exist_ok=True)
        urls = generealte_urls_list(date_list)

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


from precip.helper_functions import generate_date_list
date_list = generate_date_list('20000601', '20000605')

jtstream = JetStream()
CloudFileManager(jtstream).download(date_list)

local = LocalFileManager(os.getenv('PRECIP_DIR'))
local.download(date_list)
