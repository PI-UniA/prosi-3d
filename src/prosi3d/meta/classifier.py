"""
Abstract Base Class for data models that conduct classification upon the input data
"""

from abc import ABC, ABCMeta, abstractmethod
from .analysis import DataModel
class Classifier(DataModel):
    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for classifier-type models """
    
    @abstractmethod
    def _class_distribution(self):
        """ Output the distribution of the input data over the specified classes """
        pass
    