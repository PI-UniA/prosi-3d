from abc import ABC, ABCMeta, abstractmethod
from .analysis import DataModel
"""
Abstract Base Class for data models that conducts inferential statistics on the input data
"""
class Predictor(DataModel):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for classifier-type models """

    """ Output the correlation coefficients for the specified input data """
    @abstractmethod
    def _correlation(self):
        pass

    @abstractmethod
    def _significance(self):
        pass
