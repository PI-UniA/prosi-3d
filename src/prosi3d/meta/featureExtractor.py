"""
Abstract Base Class for preprocessors that outputs features of the raw data that are required for machine learning models
"""

from abc import ABC, ABCMeta, abstractmethod
from prosi3d.meta.preprocessor import Preprocessor
class FeatureExtractor(Preprocessor):

    """
    Keep in mind that you have to define the abstract methods inherited from Preprocessor
    """

    """ Custom, specific methods for feature-type Preprocessors """
    

    # Extract the measurements from the hdf5
    @abstractmethod
    def _read_measurements(self, hdf):
        pass

    # Replace nan values
    @abstractmethod
    def _replace_nan(self):
        pass

    # Create the FFT based on the time values
    @abstractmethod
    def _create_FFT(self):
        pass
    

    # Extract the peaks in freqency domain
    @abstractmethod
    def _find_peaks_values(self):
        pass