# -*- coding: utf-8 -*-
"""
Created on Wed May  5 18:22:37 2021

@author: ringel
"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

class EosPreprocess():

    def readDf(eostxtfile):
        """
        Reads txt-File exported via EOSPRINTAPI from openjz.txt build-preview-file
        Deletes non numeric numbers and calculates layerchanges
        
        returns df: array with vector-tuple in rows and columns: x_mm, y_mm, exposureType, partId
        returns layers: list of layerchangelineindexes starting with change from 1 to 2
        
        Args: eostxtfile
        Returns: df, layers
        """


        ###################################################################
        # Data
        ###################################################################

        global data, openjobfile, parfile

        data = R"C:\Users\ringel\Lokal\ProSi3D\Py\20210806_prosi3d-image-calibration_44x44.openjz.txt"
        openjobfile = R"C:\Users\ringel\Lokal\ProSi3D\Py\20201204_Fehlerprovokation_Brose_bjr.openjob"
        parfile = R"C:\Users\ringel\Lokal\ProSi3D\Py\par_Brose4IATP_val2.csv"

        ###################################################################
        


        df = pd.read_csv(eostxtfile, sep=',', header=None, error_bad_lines=False, warn_bad_lines=True, skiprows=4)
        
        ## re-define columnheader
        df.columns = ['x_mm', 'y_mm', 'exposureType', 'partId']
        
        # Delete non numeric letters in data
        df[df.columns[0]] = df[df.columns[0]].map(lambda x: str(x)[6:])
        df[df.columns[1]] = df[df.columns[1]].map(lambda x: str(x)[6:])
        df[df.columns[2]] = df[df.columns[2]].map(lambda x: str(x)[14:])
        df[df.columns[3]] = df[df.columns[3]].map(lambda x: str(x)[8:])
        
        # delete exposureType 0, which is just for visualization of part boundaries
        df = df.drop(df.loc[df.exposureType == ' 0'].index)
        df = df.reset_index(drop=True)
        
        # create variable for where layers change in new var layers
        layers = df[df['x_mm'].str.contains("ewdata")]
        
        # just first column is relevant here, drop others
        layers = layers.drop(['y_mm', 'exposureType', 'partId'], axis='columns')
        layers.columns = ['Layer']
        
        ## Delete lines were new layer starts and reset index numbering
        df = df.drop(layers.index, axis=0)
        df = df.reset_index(drop=True)
        return df, layers

    def df2Layers_hdf(df, layers):
        """
        Follows function readDf(). slice and save dataframe into layerwise hdf5-files.
        columns: x_mm, y_mm, exposureType, partId
        Indexes from original dataframe are used -> first index of layer n>1 is not 0
        
        Args: layers
        Returns: >saved layerwise eosprint-vector-data in hdf5 file format<
        """

        # make numbers - a lot of cpu time necessary
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
            ii = i - (lay - 1)
            df[j:ii].to_hdf(f, key='df', mode='w')
            print(f + ' von ' + size + ' Schichten gespeichert.')
            j = ii
            lay+=1
        f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
        df[j:].to_hdf(f, key='df', mode='w')
        print(f + ' of ' + size + ' Layers saved.')
        print('Original layer data from EOSPRINT have been saved to separate h5 Files. Except lines where exposureType equals zero.')
        return lay

    def __jumpAcceleration(dis, lin=0):
        '''
        Called by vecTiming_hdf(). Calculates mean jump speed for jumptimecalculation based on
        lin=0: log regression of measured values
        lin=1
        
        #better: return directly return time for "asked" jump lengths
        
        Args: dis, lin=1
        Returns: mean_jump_speed
        '''
        # damit log(<1) nicht negativ
        #da = dis*1000
        if lin == 0:
            da = dis*1000
        else:
            da = dis
        # x = distance; y = measured mean speed  
        # v_mean = -0.0001*np.power(dis, 4) + 0.0437*np.power(dis, 3) - 5.6237*np.power(dis, 2) + 273.54*dis + 513.48
        da = da.to_frame()
        da['v_mean'] = 1
        da['time'] = 2
        da.columns=['dis','v_mean', 'time']
        
        if lin == 0:
            # mean speed as log function from 0,256 mm jump distance
            # 737075ln(x) - 4E+06 | alle R2=0,8671
            # speeds below welding speeds dont make sense
            korr = 170000
            #da.v_mean.loc[da.dis > 1230] = 800000*np.log(da.dis) - 4E+06
            #da.v_mean.loc[da.dis < 1230] = 1600000 - 120000
            da.v_mean.loc[da.dis > 1230] = 787181*np.log(da.dis) - 4E+06
            da.v_mean.loc[da.dis < 1230] = 1600000 - 120000
            da.v_mean = da.v_mean/1000
        
        if lin == 1:
            # change number to layer and give this function layer numbers to apply layer-specific correction tables
            f = "jump_data" + str(582).zfill(5) + ".h5"
            dbase = pd.read_hdf(f, 'dbase')
            dbase_sort = dbase.sort_values(by=['dis_eos', 'v_mean'])
            interpol = interp1d(dbase_sort.dis_eos, dbase_sort.v_mean, bounds_error=False)
            da['v_mean'] = interpol(da.dis)
            
            #target.time_ttl.loc[target.time_ttl.isna()] = target_init.time_ttl.loc[target.time_ttl.isna()]
        if lin == 2:
            da.time = 0.0002*da.dis + 0.0008
            da.v_mean = da.dis/da.time
        
        da.v_mean.loc[da.v_mean > 5500] = 5500
        da.v_mean.loc[da.v_mean == -np.inf] = 7000
        da.v_mean.loc[da.v_mean == 0] = 0
        
        #global jumpAccs
        mean_jump_speed = da.v_mean
        return mean_jump_speed

    def vecTiming_hdf(total,lay=1,debug=0,readonly=0, changeExposure=1):
        '''
        Layerwise dataframe must be in file-name-format: eosprint_layer00001.h5
        Calculates time for each x,y point in df regarding laser and jump speeds.
        Saves timeseries to files with format: vectortimes00001.h5
        calls setSpeed() and param()
            
        Args: last layer number; optional: starting layer, debug = 1 makes eos_jump, eos_laser global variables, debug = 2 returns eos_jump, eos_laser, readonly=1 does not save
        Returns: >saves files< except debug modes give values back
        '''

        while lay <= total:
            f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
            f = "broseV2\\" + f
            #global df
            df = pd.read_hdf(f, 'df')
            # if following coordinate equals, then distance is simply zero
            
            # Calculates the difference of a Dataframe element compared with another element in the Dataframe (in previous row).
            # since it is just one column there is no axis option
            # -1 --> diff of row "minus" following row => line 1 = line 1 minus line 2 and so on
            df['dx'] = df['x_mm'].diff(periods=-1)
            df['dy'] = df['y_mm'].diff(periods=-1)
            
            # Quadrieren
            df['dx2'] = df['dx'].pow(2)
            df['dy2'] = df['dy'].pow(2)
            
            # dis: line 1 = line 1 minus line 2 and so on
            # calulate distances via pythagoras
            df['dis'] = df[['dx2','dy2']].sum(axis=1).pow(1./2)
            
            # angle of vector
            df['angle'] = np.rad2deg(np.arctan2(df['dy'], df['dx']))
            
            # line 1 = line 1 minus line 3, line 2 = line 2 minus line 4 and so on
            df['dphi'] = df['angle'].diff(periods=-2)
            
            # Shift column dphi in axis row by +1 to have "180" in the line of jump
            df.dphi=df.dphi.shift(periods=1, axis=0, fill_value=0)
            
            # correct wrong definition of contour exposureType in eos print export data
            if changeExposure == 1:
                # contours always have matching end and starting points. wrong value was set to expType = 2
                ind4Change = df.loc[(df.dis == 0) & (df.exposureType == 2)].index
                #ind4Change = df.loc[((np.abs(round(df.dphi,0))==90) | (np.abs(round(df.dphi,0))==270)) & (df.dis == 0) & (df.exposureType == 2)].index
                
                # change exposureType for found jumps
                df.loc[ind4Change, 'exposureType'] = 5
                # change exposureType for laservectors before and afterwards
                
                # muss geändert werden --> wenn vektor der letzte ist und dann plus 1: index out of range
                # wenn size 1 dann regel behalten. zus regel else wenn letzter eintrag gleich länge
                if ind4Change.size == 1:
                        if len(df) - 1 == ind4Change:
                            print('changelast failure')
                else:
                    df.loc[ind4Change+1, 'exposureType'] = 5
                df.loc[ind4Change-1, 'exposureType'] = 5
                print('Changed exposures:')
                print(df.loc[((np.abs(round(df.dphi,0))==90) | (np.abs(round(df.dphi,0))==270)) & (df.dis == 0)].exposureType.count()+1)
                
                # update eosprint_layer file 
                df[['x_mm','y_mm','exposureType','partId']].to_hdf(f, key='df', mode='w')
                
            # Call setSpeed for allocating speeds to exposureType
            # setSpeeds could be called before while loop as build parametres are constants for entire buildjob
            df['v'] = EosPreprocess.__setSpeed(df, df['exposureType'], df['partId'])
            
            # overwrite jump speeds between vector pairs (alternating from vector pairs)
            # odd line number count: vector pairs start from 2nd+3rd entry. first koordinate tuple is ignored. maybe laser initialization.
            #speed_jump = 2900
            if len(df)%2 == 1:
                # first layer
                # is first jump visible because laser was not on before?
                df.v.iloc[0::2] = EosPreprocess.__jumpAcceleration(df.dis.iloc[0::2])
            # even line count: start with first line
            else:
                # except first layer
                df.v.iloc[1::2] = EosPreprocess.__jumpAcceleration(df.dis.iloc[1::2])

            # t = s/v
            df['time'] = df['dis'].div(df['v'])
            
            ## Skywriting corrections
            
            # add timeconstant for skywriting if oneeightee
            #k_skywriting-offset around 0.00050 combined with logarithmic speed curve
            k_skywriting = 0.000475
            df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179), 'time'] = df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179), 'time'] + k_skywriting
            
            # y = 731.19*ln(x)+1437.9
            # x = distance; y = measured mean speed
            
            # may there is an additional distance rule necessary: skywriting only if endpoint is near/next to starting point
            #df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179) & (df.dis < 1) & (df.dis != 0), 'time'] = df.loc[(np.abs(df.dphi) < 181) & (np.abs(df.dphi) > 179) & (df.dis < 1) & (df.dis != 0), 'time'] + 0.46

            # cumulative sum of time
            df['cum-sum'] = df['time'].cumsum()
            
            ## first layer has odd line number count and pairs start from 2nd+3rd entry. first koordinate tuple is ignored. dunno why.
            # all the others have even line count and start from first layer
            if len(df)%2 == 1:
                df_laser = df.iloc[1::2]
                df_jump = df.iloc[0::2]
            else:
                df_laser = df.iloc[0::2]
                df_jump = df.iloc[1::2]
            
            df_laser['cum-sum'] = df_laser['time'].cumsum()
            df_jump['cum-sum'] = df_jump['time'].cumsum()
            
            (df_laser.dis == 0).sum()
            if readonly == 0:
                f = "vectortimes" + str(lay).zfill(5) + ".h5"
                df[['time','cum-sum','dis','angle', 'dphi']].to_hdf(f, key='df', mode='w')
                print(f + ' von ' + str(total) + ' gespeichert.')
            #del df
            lay += 1
        
        # why is laser and jump 0 1 flipped in debug mode?
        if debug == 1:
            global eos_laser, eos_jump
            if len(df)%2 == 1:
                # laser is len of jumps at laser start
                eos_laser = df.iloc[0::2]
                eos_jump = df.iloc[1::2]
            else:
                eos_laser = df.iloc[1::2]
                eos_jump = df.iloc[0::2]
        if debug == 2:
            if len(df)%2 == 1:
                # laser is len of jumps at laser start
                eos_laser = df.iloc[0::2]
                eos_jump = df.iloc[1::2]
            else:
                eos_laser = df.iloc[1::2]
                eos_jump = df.iloc[0::2]
            return eos_jump, eos_laser
        
    def __listpar(file):
        f = open(file, 'r')
        global df
        df = f.readlines()
        partlist = []
        paramlist = []
        i = 0
        for line in df:
            if i == 0:
                vers = line.find('creator_version')
                print(line[vers:])
                    
            pos_par = line.find('<parameter>')
            if pos_par != -1:
                s = pos_par + 11
                e = line.find('</parameter>', s)
                param = line[s:e]
                paramlist.append(param)
                
                s = prev_line.find(' name="') + 7
                e = prev_line.find('"', s)
                part = prev_line[s:e]
                partlist.append(part)
                
            prev_line = line
            i += 1
        
        parlist = pd.DataFrame(paramlist)
        parlist.to_csv('par_' + file[:-8] + '.csv', sep=';')
        return paramlist, partlist
                
    def __parByCsv(file):
        '''
        Parameter calculated by listpar() are already in the right sequence (partid iterates by appearance in openjobfile)
        Call this function instead of param()
        
        Before running this run listpar() and add speeds mm/s to column C
        '''
        df = pd.read_csv(file, sep=';')
        df = df.iloc[:,:3]
        df.columns = ['partid', 'partname', 'speed_mms']
        # partid starts counting by 1 ?
        df.partid = df.partid + 1
        speeds = df.speed_mms.to_list()
        return speeds
                
    def __param(d=data):
        '''
        reads partname and parameter from *.openjob
        works with EOSPRINT v2.6 and v2.8
        called by setSpeed()
        chronologic appearing equals partId iterating from zero within EOSPRINTAPI
        
        Args: >Openjob Filename<
        Returns: >list of speeds in row of appaerance for function setSpeed()<
        '''
        f = open(d, 'r')
        partlist = []
        paramlist = []
        df = f.readlines()
        i = 0
        # iterate openjobfile
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
            # pos equals position of part name first character
            
            # list parameters if string is found 
            if posi != -1:
                
                # pos2 equals last character of part name
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
        # build parametere DoE. Order of values in speeds equals order in EOSPrint build data file!
        # für dieses konkrete Beispiel werden im folgenden die geschwindigkeiten mit der parameterreihenfolge in der Openjobdatei synchronisiert, sodass die PartID der Stelle der richtigen Geschwindigkeit in speed enstpricht
        # syncronisation of sequence in openjobfile. partID get same order position as it's velocity in speeds
        # 
        speed = []
        for part in paramlist:
            if part == 'EOS_DirectPart' or part == 'EOS_ExternalSupport':
                pass
            else:
                j = paramdict.index(part)
                speed.append(speeds[j])
        return speed

    def __setSpeed(df, expType, partId):
        '''
        Match exposuretypes with scanspeeds considering different parametersets by partid.
        Does not consider energy input homogenization
        Must be called once per build job. is called each layer
        Calls function param()
        
        Args: df, expType, partId
        Returns: df['v']
        '''
        # Scanspeeds mm/s aus Brose Fehlerprovokationsjob
        # partboundary ist keine belichtung

        ##speed = __param(openjobfile)
        speed = EosPreprocess.__parByCsv(parfile)
        
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
        
        # if support layer width is twice part layer width
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
        df.loc[(expType == 0), 'v'] = 999999999
        #df.loc[lambda df: data == 2]
        
        return df['v']

    ## full preprocess
    #vecTiming_hdf(df2Layers_hdf(readDf(data)))