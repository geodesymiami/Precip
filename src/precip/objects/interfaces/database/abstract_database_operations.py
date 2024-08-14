from abc import ABC, abstractmethod


class AbstractDatabaseOperations(ABC):
    @abstractmethod
    def select_data(self):
        pass


    @abstractmethod
    def check_table(self):
        pass


    @abstractmethod
    def insert_data(self):
        pass