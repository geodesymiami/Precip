from precip.objects.interfaces.abstract_cloud_manager import AbstractCloudManager
from precip.objects.interfaces.credentials.abstract_credentials import AbstractCredentials
import paramiko
import os


class JetStream(AbstractCloudManager):
    def __init__(self, credential: AbstractCredentials) -> None:
        self.path = credential.path
        self.hostname = credential.hostname
        self.username = credential.user
        self.ssh = None

        # TODO Tailored to my(disilvestro) environment
        self.path_id_rsa = os.path.join(os.getenv('HOME'), credential.rsa_key)
        self.ssh_key = self.path_id_rsa


    def connect(self) -> None:
        for i in range(3):
            try:
                # Connect to the server
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=self.hostname, username=self.username, key_filename=self.ssh_key)
                self.ssh = ssh
                print('-'*50)
                print('Connected to the server\n')
                break

            except paramiko.SSHException as e:
                print(f"Attempt {i+1} failed to connect to the server: {e}")
                # Limit reached
                if i > 2:
                    self.ssh = None


    def open_sftp(self):
        self.sftp = self.ssh.open_sftp()
        print('-'*50)
        print('SFTP connection opened\n')


    def check_connected(self) -> bool:
        return self.ssh and self.ssh.get_transport() and self.ssh.get_transport().is_active()


    def close(self) -> None:
        self.ssh.close()
        print('Connection closed')