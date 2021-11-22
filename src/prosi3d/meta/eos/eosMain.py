# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 14:21:51 2021

@author: ringel
"""
from prosi3d.meta.eos.eosPreprocess import EosPreprocess
from prosi3d.meta.eos.eosProcess import EosProcess

class EosMain():

    def main(data):
        '''
        read eosprintapi export and save layerwisedata
        
        Args: <filepath>
        Returns: 
        '''
        ## preprocess
        
        # save layerwise data
        layCount = EosPreprocess.df2Layers_hdf(EosPreprocess.readDf(data))
        
        # calculate and save timing
        # edit/check velocities in eos_preprocess line 331 "speeds" and line 358 ff. before
        eos_jump, eos_laser = EosPreprocess.vecTiming_hdf(layCount)
        
        timeSeries = EosProcess.createTimeseries(layCount)