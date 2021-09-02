from abc import ABC, ABCMeta, abstractmethod

""" Abstract Base Class for every class manipulating or extracting information from the measured data """
class Preprocessor(ABC):
    """ 
    Top-level (abstract) methods that have to be inherited and re-defined by the sub-classes
    """
    @abstractmethod
    def get_data(self):
        pass

    @abstractmethod
    def process(self):
        pass

    @abstractmethod
    def write(self):
        pass
