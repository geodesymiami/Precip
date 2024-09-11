from abc import ABC, abstractmethod
from precip.objects.interfaces.plotter.plotter import Plotter


class EventsPlotter(Plotter):
    @abstractmethod
    def plot_elninos(self):
        pass


    @abstractmethod
    def plot_eruptions(self):
        pass