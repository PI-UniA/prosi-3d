from abc import ABC, ABCMeta, abstractmethod
from analysis import DataModel
"""
Abstract Base Class for data models that conduct classification upon the input data
"""
class Classifier(DataModel):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for classifier-type models """
    
    """ Output the distribution of the input data over the specified classes """
    @abstractmethod
    def class_distribution(self):
        pass
    