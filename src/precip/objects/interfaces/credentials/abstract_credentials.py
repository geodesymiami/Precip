from abc import ABC, abstractmethod

class AbstractCredentials(ABC):
    @abstractmethod
    def get_credentials(self):
        pass