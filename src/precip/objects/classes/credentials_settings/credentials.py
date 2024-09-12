import os
from precip.objects.interfaces.credentials.abstract_credentials import AbstractCredentials


class PrecipVMCredentials(AbstractCredentials):
    def __init__(self):
        self.get_credentials()


    def get_credentials(self):
        self.hostname = os.getenv('REMOTEHOST_PRECIP')
        self.user = os.getenv('REMOTEUSER')
        #Tailored to my (disilvestro) environment
        self.rsa_key = '.ssh/id_rsa'
        self.path = os.getenv('PRECIP_DIR')