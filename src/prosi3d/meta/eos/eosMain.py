# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 14:21:51 2021

@author: ringel
"""


def main(data):
    '''
    read eosprintapi export and save layerwisedata
    
    Args: <filepath>
    Returns: 
    '''
    ## preprocess
    
    # save layerwise data
    layCount = df2Layers_hdf(readDf(data))
    
    # calculate and save timing
    # edit/check velocities in eos_preprocess line 331 "speeds" and line 358 ff. before
    vecTiming_hdf(layCount)
    
    createTimeseries(layCount)