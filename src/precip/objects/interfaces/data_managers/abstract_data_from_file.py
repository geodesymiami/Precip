from abc import abstractmethod
from interfaces import AbstractFileHandler


class AbstractDataFromFile(AbstractFileHandler):
    @abstractmethod
    def process_file(self):
        pass