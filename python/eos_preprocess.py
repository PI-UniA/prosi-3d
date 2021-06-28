# -*- coding: utf-8 -*-
"""
Created on Wed May  5 18:22:37 2021

@author: ringel
"""

import numpy as np
import pandas as pd

###################################################################
# Data
###################################################################

data = R"C:\Users\ringel\Lokal\ProSi3D\Py\20210427_316L_QuAFD_Zug-Kerbe_Baubarkeit-Demo.openjz.txt"
openjobfile = R"C:\Users\ringel\Lokal\ProSi3D\Py\20210427_316L_QuAFD_Zug-Kerbe_Baubarkeit-Demo.openjob"

###################################################################


def readDf(eostxtfile):
    ## return EOSPRINT SDK Export text file in pandas dataframe df
    ## return linenumbers of layerchanges starting with layer 2 in layers
#    global df, layers
    
    df = pd.read_csv(eostxtfile, sep=',', header=None, error_bad_lines=False, warn_bad_lines=True, skiprows=4)
    
    ## re-define columnheader
    df.columns = ['x_mm', 'y_mm', 'exposureType', 'partId']
    
    ## CLEANUP: Delete non numeric letters in data
    # x_mm, y_mm, exposureType, partId
    df[df.columns[0]] = df[df.columns[0]].map(lambda x: str(x)[6:])
    df[df.columns[1]] = df[df.columns[1]].map(lambda x: str(x)[6:])
    df[df.columns[2]] = df[df.columns[2]].map(lambda x: str(x)[14:])
    df[df.columns[3]] = df[df.columns[3]].map(lambda x: str(x)[8:])
    
    # if there are non-numeric errors:
#    df[df.columns[2]] = df[df.columns[2]].map(lambda x: int(x)[14:] if str(x).isdigit() else str(x)[14:]) 
#    df[df.columns[3]] = df[df.columns[3]].map(lambda x: int(x)[8:] if str(x).isdigit() else str(x)[8:])
    
    # delete exposureType 0, which is just for visualising part boundaries
    df = df.drop(df.loc[df.exposureType == ' 0'].index)
    df = df.reset_index(drop=True)
    
    ## Lines where Layers change in new var layers
    layers = df[df['x_mm'].str.contains("ewdata")]
    # just first column needed giving index of layerchanges
    layers = layers.drop(['y_mm', 'exposureType', 'partId'], axis='columns')
    layers.columns = ['Layer']
    
    ## Delete lines were new layer starts and reset index numbering
    df = df.drop(layers.index, axis=0)
    df = df.reset_index(drop=True)
    return df, layers

def df2Layers_hdf(df, layers):
    ## save df from readDf() to layerwise files
    # df2Layers_hdf(df, layers)
    # return layer amount
    
    # make numbers - need a lot of cpu time
    df['x_mm'] = pd.to_numeric(df['x_mm'],downcast='float')
    df['y_mm'] = pd.to_numeric(df['y_mm'],downcast='float')
    df['exposureType'] = pd.to_numeric(df['exposureType'],downcast='integer')
    df['partId'] = pd.to_numeric(df['partId'],downcast='integer')
    
    size = layers.shape[0] + 1
    size = str(size)
    j = 0
    lay = 1
    for i, row in layers.iterrows():
        f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
        #fopen = open(f, "wb")
        ii = i - (lay - 1)
        df[j:ii].to_hdf(f, key='df', mode='w')
        #fopen.close()
        print(f + ' von ' + size + ' Schichten gespeichert.')
        j = ii
        lay+=1
    f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
    # vorher df[j:-1]. dabei fehlte letzte Zeile und Vektorplot wurde durch ungerade anzahl falsch berechnet.
    # manuell korrigiert in der datei. folgezeile nicht getestet.
    df[j:].to_hdf(f, key='df', mode='w')
    print(f + ' von ' + size + ' Schichten gespeichert.')
    print('Original layer data from EOSPRINT have been saved to separate h5 Files. Except lines where exposureType equals zero.')
    return size

def vecTiming_hdf(total,lay=1):
    # eingabe: bis = total; von = lay vecTiming_hdf(bis:von)
    # calls setSpeed() and thereby param()
    ## Calculate time for each x,y point in df regarding laser speeds.
    # each two lines are calculated --> half vectors are jumps
    ## total ist die Anzahl von Dateien bzw. Schichten. Achtung namensgebung beachten
    #lay = 1
    while lay <= total:
        f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
        global df
        df = pd.read_hdf(f, 'df')
        # if following coordinate equals, then distance is simply zero
        
        # Calculates the difference of a Dataframe element compared with another element in the Dataframe (in previous row).
        #
        ############################
        #   since it is just one column there is no axis option
        ############################
        # -1 --> diff of row "minus" following row
        df['dx'] = df['x_mm'].diff(periods=-1)
        df['dy'] = df['y_mm'].diff(periods=-1)
        # Quadrieren
        df['dx2'] = df['dx'].pow(2)
        df['dy2'] = df['dy'].pow(2)
        # calulate distances via pythagoras
        df['dis'] = df[['dx2','dy2']].sum(axis=1).pow(1./2)
        
        # Call setSpeed for allocating speeds regardings exposureType
        # setSpeeds could be called before while loop as parametres are fixed for entire buildjob
        df['v'] = setSpeed(df, df['exposureType'], df['partId'])
        
        # angle of vektor
        df['angle'] = np.rad2deg(np.arctan2(df['dy'], df['dx']))
        
        ## overwrite jump speeds between vector pairs (alternating from vector pairs)
        # odd line number count: vector pairs start from 2nd+3rd entry. first koordinate tuple is ignored. maybe laser initialization.
        # 5000 is more realistic based on measured values
        if len(df)%2 == 1:
            df.iloc[0::2,9] = 5000
        # even line count: start with first line
        else:
            df.iloc[1::2,9] = 5000

        ## Time based on speeds 
        # t = s/v
        df['time'] = df['dis'].div(df['v'])
        
        #######################################################################
        ## Time corrections
        # Skywriting
        df['dphi'] = df['angle'].diff(periods=-2)
        # Muss versetzt werden um eins in den zeilen. aktuell wird jetzt die laserzeit überschrieben
        df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179), 'time'] = df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179), 'time'] + 0.46
        # muss hier noch eine Abstandsklausel dazu? Skywriting nur wenn direkt nebeneinander?
        #df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179) & (df.dis < 1) & (df.dis != 0), 'time'] = df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179) & (df.dis < 1) & (df.dis != 0), 'time'] + 0.46
        # distance
        
        #######################################################################
        
        # cumulative sum of time
        df['cumsum'] = df['time'].cumsum()
        
        ## first layer has odd line number count and pairs start from 2nd+3rd entry. first koordinate tuple is ignored. dunno why.
        # all the others have even line count and start from first layer
        if len(df)%2 == 1:
            df_laser = df.iloc[1::2]
            df_jump = df.iloc[0::2]
        else:
            df_laser = df.iloc[0::2]
            df_jump = df.iloc[1::2]
        
        df_laser['cumsum'] = df_laser['time'].cumsum()
        df_jump['cumsum'] = df_jump['time'].cumsum()
        
        

        #dfout.loc[dfout.exposureType == 0, 'dis'].describe()
        
#        fig1 = df_laser['dis'].plot.hist(bins=64, alpha=1)
#        fig2 = df_jump['dis'].plot.hist(bins=64, alpha=0.5)
#        fig1.set_yscale('log')
#        fig2.set_yscale('log')
        
        (df_laser.dis == 0).sum()
        
                        
        f = "vectortimes" + str(lay).zfill(5) + ".h5"
        df[['time','cumsum','dis','angle', 'dphi']].to_hdf(f, key='df', mode='w')
        print(f + ' von ' + str(total) + ' gespeichert.')
        #del df
        lay += 1
              
def param(d=data):
    # reads partname and parameter from *.openjob
    # calls param()
    # chronologic appearing equals partId iterating from zero within EOSPRINTAPI
    #global partlist, paramlist, paramdict
    #global speed
    f = open(d, 'r')
    partlist = []
    paramlist = []
    df = f.readlines()
    i = 0
    # Zeilenweise datei durhclaufen
    for line in df:
        
        # file looks a bit different wether its EOSPRINT version
        if i == 0:
            vers = line.find('creator_version')
            if line[vers+17:vers+20] == '2.6':
                print('EOSPRINT V2.6')
                case = 0
            if line[vers+17:vers+20] == '2.8':
                print('EOSPRINT V2.8')
                case = 1
        if case == 0:
            pos = line.find('parts\\')
            posi = pos
            pos = pos + 6
        if case == 1:
            pos = line.find('}" name=')
            posi = pos
            pos = pos + 9
        # wenn string auftaucht also nicht -1 ist. 
        if posi != -1:
            pos2 = line.find('"', pos)
            partlist.append(line[pos:pos2] + '.stl')
            param = df[i+1]
            s = param.find('<parameter>')
            e = param.find('</parameter>')
            param = param[s+11:e]
            paramlist.append(param)
        i += 1
    paramdict = list(dict.fromkeys(paramlist))
    paramdict = sorted(paramdict)
    paramdict = paramdict[2:]
    speeds = [500, 750, 1000, 1250, 500, 750, 1000, 1250, 500, 750, 1000, 1250, 500, 750, 1000, 1250, 500, 750, 1000, 1250]
    # Parametervaration Schichtuberwachung_Dichte_01 - 20 sind aufsteigend in EOSPrint sortiert. Reihung in speeds folgt dieser Sortierung.
    # für dieses konkrete Beispiel werden im folgenden die geschwindigkeiten mit der Bauteilreihenfolge in der Openjobdatei synchronisiert, sodass die PartID der Stelle der richtigen Geschwindigkeit in speed enstpricht
    speed = []
    for part in paramlist:
        if part == 'EOS_DirectPart' or part == 'EOS_ExternalSupport':
            pass
        else:
            j = paramdict.index(part)
            speed.append(speeds[j])
    return speed

def setSpeed(df, expType, partId):
    # does not consider energy input homogenization
    # param muss irgendwann mindestens einmal aufgerufen werden für global speed
#    global speed
    speed = param(openjobfile)
    # Scanspeeds mm/s aus Brose Fehlerprovokationsjob
    # partboundary ist keine belichtung
    
    # DirectPart MS1 42CrMo5
#    v_hatch_in = 1010
#    v_hatch_up = 675
#    v_hatch_do = 2000
#    v_kontur_std = 370
#    v_kontur_do = 4000
#    v_kontur_up = 400
#    v_edge = 700
#    v_supp = 1400
    
    # DirectPart 316L
    v_hatch_in = 928.1
    v_hatch_up = 514.9
    v_hatch_do = 951.2
    v_kontur_std = 446.9
    v_kontur_do = 4000
    v_kontur_up = 447.1
    v_edge = 900
    v_supp = 675
    v_suppdouble = 1269.5
    
    v_jump = 5000
    
    df['v'] = 5000
    # expType. specific types get specific speed
    df.loc[(expType == 1), 'v'] = v_hatch_do
    df.loc[(expType == 2), 'v'] = v_hatch_in
    for index, val in enumerate(speed):
        df.loc[(expType == 2) & (partId == index), 'v'] = speed[index]
    
    df.loc[(expType == 3), 'v'] = v_hatch_up
    df.loc[(expType == 4), 'v'] = v_kontur_do
    df.loc[(expType == 5), 'v'] = v_kontur_std
    df.loc[(expType == 6), 'v'] = v_kontur_up
    df.loc[(expType == 7), 'v'] = v_edge
    # not really safe if this is support exposure or some EOSPRINT GUI thing
    df.loc[(expType == 8), 'v'] = v_supp
    # hatchgap (?)
    df.loc[(expType == 9), 'v'] = v_jump
    # if contour does not have up or downskin
    df.loc[(expType == 10), 'v'] = v_kontur_std
    df.loc[(expType == 11), 'v'] = v_jump
    # boarder lines for EOSPRINT GUI - no exposure, no travel time in process
    df.loc[(expType == 0), 'v'] = 9999999
    #df.loc[lambda df: data == 2]
    
   
    return df['v']

## full preprocess
#vecTiming_hdf(df2Layers_hdf(readDf(data)))
