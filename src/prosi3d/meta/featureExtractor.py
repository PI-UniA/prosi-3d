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
    
    ###Diese Methode habe ich nicht verwendet
    #""" Extract the RMS of the signal """
    #@abstractmethod
    #def _rms(self):
    #    pass

    """ Extract the measurements from the hdf5 """
    @abstractmethod
    def _read_measurements(self, hdf):
        pass

    """ Replace nan values """
    @abstractmethod
    def _replace_nan(self):
        pass

    """ Create the FFT based on the time values """
    @abstractmethod
    def _create_FFT(self):
        pass
    

    """ Extract the peaks in freqency domain """
    @abstractmethod
    def _find_peaks_values(self):
        pass
    
    """assignment position of the laser (x,y) to the measurements (time signal) """
    @abstractmethod
    def assignment_measurements_to_position(self, hdf_name):
        pass