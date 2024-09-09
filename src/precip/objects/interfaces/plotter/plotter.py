from abc import ABC, abstractmethod


class Plotter(ABC):
    @abstractmethod
    def plot(self):
        pass


    def modify_dataframe(self):
        pass