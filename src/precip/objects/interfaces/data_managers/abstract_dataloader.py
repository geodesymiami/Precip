from abc import abstractmethod
from interfaces import AbstractDataSource


class AbstractDataLoader(AbstractDataSource):
    @abstractmethod
    def load_data(self):
        pass