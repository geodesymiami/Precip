from abc import ABC, abstractmethod
from interfaces import Plotter


class EventsPlotter(Plotter):
    @abstractmethod
    def plot_elninos(self):
        pass


    @abstractmethod
    def plot_eruptions(self):
        pass