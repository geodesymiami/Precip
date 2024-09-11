from abc import ABC, abstractmethod

class AbstractFileManager(ABC):
    @abstractmethod
    def download(self, date_list, parallel=5):
        pass

    @abstractmethod
    def check_files(self):
        pass