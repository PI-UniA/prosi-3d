from abc import ABC, ABCMeta, abstractmethod

""" Abstract Base Class for every class analyzing the measured data """
class DataModel(ABC):
    """ 
    Top-level (abstract) methods that have to be inherited and re-defined by the sub-classes
    """
    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def analyze(self):
        pass
