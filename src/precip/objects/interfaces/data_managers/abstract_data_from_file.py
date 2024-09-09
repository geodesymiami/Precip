from abc import abstractmethod
from precip.objects.interfaces.data_managers.abstract_file_handler import AbstractFileHandler


class AbstractDataFromFile(AbstractFileHandler):
    @abstractmethod
    def process_file(self):
        pass