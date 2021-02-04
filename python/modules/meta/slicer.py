from abc import ABC, ABCMeta, abstractmethod
from preprocessor import Preprocessor
"""
Abstract Base Class for preprocessors that slice and group the raw data
"""
class Slicer(Preprocessor):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for slicer-type Preprocessors """
    
    """ Search for slicing points """
    @abstractmethod
    def _get_slicing_points(self):
        pass
    