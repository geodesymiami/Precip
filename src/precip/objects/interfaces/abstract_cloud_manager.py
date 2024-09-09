from abc import ABC, abstractmethod

class AbstractCloudManager(ABC):
    @abstractmethod
    def connect(self):
        pass


    @abstractmethod
    def open_sftp(self):
        pass


    @abstractmethod
    def check_connected(self):
        pass


    @abstractmethod
    def close(self):
        pass
