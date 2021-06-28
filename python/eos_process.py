# -*- coding: utf-8 -*-
"""
Created on Wed May  5 18:31:43 2021

@author: ringel
"""

import numpy as np
import pandas as pd

def getXYlin(timex, layer):
    ## returns exact position x-y position for entered timevalue xtime, ytime and partId plus exposureType
    ## partId and exposureType return -1 if pair not equal
    
    # df contains of time per vector, cumsum of time, length (dis) of vector 
    f = "vectortimes" + str(layer).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    
    # dg contains of pairs of points for vectors x_mm, y_mm, exposureType and partId from EOSPRINT export
    g = "eosprint_layer" + str(layer).zfill(5) + ".h5"
    dg = pd.read_hdf(g, 'df')
    
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
        # column cumsum is one
        if  df.iloc[i,1] > timex:
            while df.iloc[i,1] > timex:
                i-=1 
        else:
            while df.iloc[i,1] <= timex:
                i+=1
            i-=1
    
    # times t1, t2 before/after entered timevalue
    t1 = df.iloc[i,1]
    t2 = df.iloc[i+1,1]
    print('Suche: ' + str(istart) + ' -> ' + str(i))
    print('Zeit: ' + str(timex - t1), str(timex), str(t2 - timex))
    print('Zeit: ' + str(t1), str(timex), str(t2))
    
    # linear calculation: relative time difference equals relative vector length difference to point of interest
    tdiff = timex - t1
    diff = tdiff/(t2-t1)
    # column dis is two
    diserr = diff*df.iloc[i, 2]
    print(str(diff*100) + ' % timediff to t1.')
    print(str(diserr) + ' of ' + str(df.iloc[i, 2]) + ' mm absolute distance to pnt1.')
    
    
    x1 = dg.iloc[i,0]
    x2 = dg.iloc[i+1,0]
    y1 = dg.iloc[i,1]
    y2 = dg.iloc[i+1,1]
    
    xdis = x2 - x1
    ydis = y2 - y1
    print(str(xdis) + ' mm x-distance')
    print(str(ydis) + ' mm y-distance')
    
    xtime = x1 + xdis*diff
    ytime = y1 + ydis*diff
    
    print()
    print(str(xtime - x1), str(xtime), str(x2 - xtime))
    print(str(x1), str(xtime), str(x2))
    print(str(ytime - y1), str(ytime), str(y2 - ytime))
    print(str(y1), str(ytime), str(y2))
    print()
#    , str(diff), str(diserr))
    
    #partId is column three
    if dg.iloc[i,3] == dg.iloc[i+1,3]:
        partId = dg.iloc[i,3]
    else:
        partId = -1
        
    if dg.iloc[i,2] == dg.iloc[i+1,2]:
        exposure = dg.iloc[i,2]
    else:
        exposure = -1
    
    print(dg.iloc[i,:], dg.iloc[i+1,:])
    
    return xtime, ytime, int(partId), int(exposure)