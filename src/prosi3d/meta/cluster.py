from abc import ABC, ABCMeta, abstractmethod
from .analysis import DataModel
"""
Abstract Base Class for data models that conduct clustering upon the input data
"""
class Cluster(DataModel):

    """
    Keep in mind that you have to define the abstract methods inherited from DataModel
    """

    """ Custom, specific methods for classifier-type models """
    
    """ Output the number of identified clusters for the specified input data """
    @abstractmethod
    def _num_clusters(self):
        pass
    