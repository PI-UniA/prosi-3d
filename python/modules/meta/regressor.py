from abc import ABC, ABCMeta, abstractmethod
from analysis import DataModel
"""
Abstract Base Class for data models that conduct regression upon the input data
"""
class Regressor(DataModel):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for classifier-type models """
    
    """ Output the regression coefficient for the specified input data """
    @abstractmethod
    def _coefficient(self):
        pass
    