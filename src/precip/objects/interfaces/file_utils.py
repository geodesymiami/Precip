from abc import ABC, abstractmethod

class AbstractFileUtils(ABC):
    @abstractmethod
    def get_date(self):
        pass


    @abstractmethod
    def get_attributes(self):
        pass