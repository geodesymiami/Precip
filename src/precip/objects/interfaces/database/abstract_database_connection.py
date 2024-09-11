from abc import ABC, abstractmethod


class AbstractDatabaseConnection(ABC):
    @abstractmethod
    def connect(self):
        pass


    @abstractmethod
    def close(self):
        pass