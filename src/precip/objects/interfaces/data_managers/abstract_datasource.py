from abc import ABC, abstractmethod


class AbstractDataSource(ABC):
    @abstractmethod
    def get_data(self):
        pass