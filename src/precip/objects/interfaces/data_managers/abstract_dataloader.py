from abc import abstractmethod
from precip.objects.interfaces.data_managers.abstract_datasource import AbstractDataSource


class AbstractDataLoader(AbstractDataSource):
    @abstractmethod
    def load_data(self):
        pass