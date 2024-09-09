from precip.objects.interfaces.abstract_cloud_manager import AbstractCloudManager
from src.precip.config import PATH_JETSTREAM
import paramiko
import os

class JetStream(AbstractCloudManager):
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


    def open_sftp(self):
        self.sftp = self.ssh.open_sftp()
        print('SFTP connection opened')


    def check_connected(self) -> bool:
        return self.ssh and self.ssh.get_transport() and self.ssh.get_transport().is_active()


    def close(self) -> None:
        self.ssh.close()
        print('Connection closed')