from abc import ABC, ABCMeta, abstractmethod
from .preprocessor import Preprocessor
"""
Abstract Base Class for preprocessors that outputs features of the raw data that are required for machine learning models
"""
class FeatureExtractor(Preprocessor):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for feature-type Preprocessors """
    
    """ Extract the RMS of the signal """
    @abstractmethod
    def _rms(self):
        pass
    