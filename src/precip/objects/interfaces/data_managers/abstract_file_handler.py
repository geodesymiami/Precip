from abc import ABC, abstractmethod


class AbstractFileHandler(ABC):
    @abstractmethod
    def check_duplicates(self):
        pass


    @abstractmethod
    def list_files(self):
        pass