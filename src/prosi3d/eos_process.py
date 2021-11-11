# -*- coding: utf-8 -*-
"""
Created on Wed May  5 18:31:43 2021

@author: ringel
"""

import numpy as np
import pandas as pd

def getXYlin(timex, layer, df=[], dg=[]):
    '''
    returns exact position x-y position for entered timevalue xtime, ytime and partId plus exposureType
    partId and exposureType return -1 if pair not equal
    df contains of time per vector, cumsum of time, length (dis) of vector
    
    Args: timex, layer
    Returns: xtime, ytime, int(partId), int(exposure)
    '''
    if len(df) == 0 or len(dg) == 0:
        batch = 0
    else:
        batch = 1
    
    # if called by createTimeseries() df and dg are arguments.
    if len(df) == 0:
        f = "vectortimes" + str(layer).zfill(5) + ".h5"
        df = pd.read_hdf(f, 'df')
        # 'time','cum-sum','dis','angle', 'dphi'
    if len(dg) == 0:
        # dg contains of pairs of points for vectors x_mm, y_mm, exposureType and partId from EOSPRINT export
        g = "eosprint_layer" + str(layer).zfill(5) + ".h5"
        dg = pd.read_hdf(g, 'df')
        # 'x_mm','y_mm','exposureType','partId'
    
    #print('len(df): ' + str(len(df)) + '; len(dg): ' + str(len(dg)))

    
    # total time per layer. equals last entry of cumsum. if greater then entered value raise failure
    tsum = sum(df['time'])
    if timex > tsum:
        raise SystemExit("Time entered is higher than layertime.")
    else:
        
        # rule of three predicts index istart of entered time on dataframe df
        # forward / backward moving through df if predicted timevalue higher/smaller then entered time
        # result is index of line before entered timevalue
        pred = timex / tsum
        i = int(round(pred * len(df),0))
        istart = i
        # cumsum is column 1.
        if  df.iloc[i,1] > timex:
            while df.iloc[i,1] > timex:
                i-=1 
        else:
            while df.iloc[i,1] <= timex:
                i+=1
            i-=1
    
    exposure = dg.iloc[i,2]
    # line n has distance information for line n to n+1
    # first layer has odd/uneven row count
    if len(dg)%2 == 1:
        # first layer
        if i%2 == 0:
            exposure = -2
        if batch == 0:
            laser = df.iloc[1::2]
            jump = df.iloc[0::2]
    # even line count: start with first line
    else:
        # except first layer
        if i%2 == 1:
            exposure = -2
        if batch == 0:
            laser = df.iloc[0::2]
            jump = df.iloc[1::2]

    # times t1, t2 before/after entered timevalue
    t1 = df.iloc[i,1]
    t2 = df.iloc[i+1,1]
    
    # linear calculation: relative time difference equals relative vector length difference to point of interest
    tdiff = timex - t1
    diff = tdiff/(t2-t1)
    # column dis is two
    #diserr = diff*df.iloc[i, 2]
    
    if batch == 0:
        lasercs = laser['time'].cumsum().max()
        jumpcs = jump['time'].cumsum().max()
        print('cumsum laser: ' + str(lasercs) + ' s; cumsum jump: ' + str(jumpcs) + ' s')
        print('Search starts in line: ' + str(istart) + '. Value found after line: ' + str(i))
        #print('Zeit: ' + str(timex - t1), str(timex), str(t2 - timex))
        print('Time: ' + str(t1), str(timex), str(t2))
        print('progress of vector: ' + str(diff*100) + ' %')
        print('geometric length of vector: ' + str(df.iloc[i, 2]) + ' mm')
        print('temporal length of vector: ' + str(df.iloc[i, 0]) + ' s')
    
    # start/end koordinates
    x1 = dg.iloc[i,0]
    x2 = dg.iloc[i+1,0]
    y1 = dg.iloc[i,1]
    y2 = dg.iloc[i+1,1]
    
    # distances
    xdis = x2 - x1
    ydis = y2 - y1
    
    # actual coordinate for entered timex
    xtime = x1 + xdis*diff
    ytime = y1 + ydis*diff
    
    #partId is column three
    if dg.iloc[i,3] == dg.iloc[i+1,3]:
        partId = dg.iloc[i,3]
    else:
        partId = -1
        
#    if dg.iloc[i,2] == dg.iloc[i+1,2]:
#        exposure = dg.iloc[i,2]
#    else:
#        exposure = -1
    
    # more features relevant? angle to flow or recoating direction, progress of vector, total length of vector
    return xtime, ytime, int(partId), int(exposure)

def createTimeseries(layCount, f_sample=50000, init=1):
    step = 1/f_sample
    
    # loop through layer
    for lay in range(init, layCount+1):
        f = "vectortimes" + str(lay).zfill(5) + ".h5"
        df = pd.read_hdf(f, 'df')
        # 'time','cum-sum','dis','angle', 'dphi'
        g = "eosprint_layer" + str(lay).zfill(5) + ".h5"
        dg = pd.read_hdf(g, 'df')
        # 'x_mm','y_mm','exposureType','partId'
        # more efficient if stats would be saved in separate variable via vecTiming_hdf() to just read this variable
        totaltime = df['cum-sum'].iloc[-1]
        f = np.arange(0.00006, totaltime+step, step)
        timeseries = pd.DataFrame(f)
        timeseries.columns = ['time']
        timeseries['x'] = np.nan
        timeseries['y'] = np.nan
        timeseries['part'] = np.nan
        timeseries['exposure'] = np.nan
        
        # loop through samples
        for sample in f:
            x, y, part, exposure = getXYlin(sample, lay, df, dg)
            timeseries['x'].loc[timeseries.time == sample] = x
            timeseries['y'].loc[timeseries.time == sample] = y
            timeseries['part'].loc[timeseries.time == sample] = part
            timeseries['exposure'].loc[timeseries.time == sample] = exposure
            
            if round(sample%0.2,5) == 0.0:
                print(str(sample) + ' of ' + str(totaltime))
        
        h = "timeseries" + str(lay).zfill(5) + ".h5"
        timeseries.to_hdf(h, 'timeseries')
        del timeseries
            
    
    
    
    
    
    