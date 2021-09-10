"""
Abstract Base Class for every class manipulating or extracting information from the measured data
"""

from abc import ABC, ABCMeta, abstractmethod

class Preprocessor(ABC):
    """ 
    Top-level (abstract) methods that have to be inherited and re-defined by the sub-classes
    """

    @abstractmethod
    def get_data(self):
        """ Abtract class for extracting the measurements of the specific sensor """
        pass

    @abstractmethod
    def process(self):
        """ Abstract class for converts to frequency domain in order to detect conspicuous peaks """
        pass

    @abstractmethod
    def write(self):
        """ Abstract class for printing the x values (frequency) and the y values (spectral power density) """
        pass
