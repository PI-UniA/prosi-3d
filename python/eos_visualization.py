# -*- coding: utf-8 -*-
"""
Created on Wed May  5 18:28:58 2021

@author: ringel
"""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

def describeLayer(layer):
    f = "vectortimes" + str(layer).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    
    # odd line number: use pairs starting from second line - laser adjust (?)
    if len(df)%2 == 1:
            df_laser = df.iloc[1::2]
            df_jump = df.iloc[0::2]
    # even line number: use pairs starting from first line
    else:
        df_laser = df.iloc[0::2]
        df_jump = df.iloc[1::2]
    
    df_laser['cumsum'] = df_laser['time'].cumsum()
    df_jump['cumsum'] = df_jump['time'].cumsum()
    
    # Max cumsum of total layer time equals cumsum of only laser times -> strange.
    # but total time with grabXY() equals with sum of laser plus jump times
    print(df.describe())
    
    # some laser vectors are zero length. makes no sense
    print(df_laser[df_laser['dis'] == 0].describe())
    print(df_jump.describe())
    print(df_laser.describe())
    print('Laser: ' + str(df_laser['dis'].max()) + ' mm. Jump: ' + str(df_jump['dis'].max()) + ' mm.')
    print('Laser: ' + str(df_laser['cumsum'].max()) + ' s. Jump: ' + str(df_jump['cumsum'].max()) + ' s.')
    print('Anzahl Laser-Vektoren: ' + str(len(df_laser)))
    
    #dfout.loc[dfout.exposureType == 0, 'dis'].describe()
    #return df_laser

def setColor(expType):
    switch={
            # hatch
            # 0:'mediumspringgreen',# Ansicht EOSprint
            # dunkler -> downskin, heller -> upskin
            1:'seagreen',           # down
            2:'mediumspringgreen',  # in
            3:'springgreen',        # up
            # contour
            4:'darkviolet',         # down
            5:'mediumorchid',       # in
            6:'magenta',            # up
            10:'violet',
            # edge
            7:'orangered',
            # support
            8:'dodgerblue',
            # jump
            9:'darkorange',
            11:'darkorange'
        }
    return switch.get(expType, 'black')
    
def pfeile(lay,pdf=0,color_vector=0,jumps=0):
    # jumps = 1 dreht die reihenfolge um und plottet die sprungwege
    # pdf = 1 speichert pdf anstelle inteaktiver grafik mit qt5
    # color_vector färbt denjenigen vector farbig ein - ganze zahl größer null
    # backend festlegen: interaktive grafik oder 
    # calls setColor()
    if pdf == 0:
        matplotlib.use('Qt5Agg')
    else:
        matplotlib.use('pdf')
    # part specific colors. vector specific colors - anpassen. sprünge andersfarbig als teile
    # dont use second lines. sometimes directlly following vectors occure --> skywriting when following vector tuple equals?
    f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    
    df.reset_index(drop=True, inplace=True)
    print(df.head(4))
    print(df.tail(4))
    
    #size definition for plotting in inches
    plt.figure(figsize=(96,96))
    ax = plt.axes()
    ax.set_aspect('equal')
    plt.xlim(0, 250)
    plt.ylim(0, 250)
    
    ## first layer has odd line number count
    # odd line numbers: skip first line (index 0) and use then following pairs
    if len(df)%2 == 1:
        a = 1
        if jumps==1:
            a = 0
    # even line numbers: use following pairs starting with first line 
    else:
        a = 0
        if jumps==1:
            a = 1
    if jumps == 1 and color_vector != 0:
        color_vector = color_vector*2+1
    
    for i, row in df.iterrows():
        if i%2 == a:
            if color_vector != 0 and color_vector == i:
                col = 'crimson'
            else:
                col = setColor(df.iloc[i,2])
            j = i + 1
            vec = [df.iloc[i,0], df.iloc[i,1], df.iloc[j,0]-df.iloc[i,0], df.iloc[j,1]-df.iloc[i,1]]
            ax.arrow(*vec, head_width=0.05, head_length=0.1, color=col)
        #plt.quiver(*vec)
        #print(vec)
        if i + 1 == len(df) -1:
            break
    print('Count of vectorpairs:')
    print(df.groupby('exposureType').count())
    #plt.show()
    #time.sleep(180)
    if pdf == 1:
        plt.savefig(f[0:19] + '.pdf', format='pdf', dpi=600)
        #plt.savefig(f[0:19] + '_2.svg', format='svg')
        #plt.savefig(f[0:19] + '.png', dpi=50)
        plt.close()
        del(df)
        matplotlib.use('Qt5Agg')

def batchPfeile(total):
    lay = 1
    while lay <= total:
        pfeile(lay,1)
        lay += 1