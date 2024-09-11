from abc import abstractmethod
from .abstract_file_manager import AbstractFileManager

class AbstractCloudFileManager(AbstractFileManager):
    @abstractmethod
    def cloud_download(self):
        pass

    @abstractmethod
    def create_temp_file(self):
        pass