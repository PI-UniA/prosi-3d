from abc import ABC, ABCMeta, abstractmethod
from .preprocessor import Preprocessor
"""
Abstract Base Class for preprocessors that outputs descriptive statistics of the raw data
"""
class Descriptor(Preprocessor):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for descriptor-type Preprocessors """
    
    """ Generate statistical moments """
    @abstractmethod
    def _moments(self):
        pass
    