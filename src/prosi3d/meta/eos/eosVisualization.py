# -*- coding: utf-8 -*-
"""
Created on Wed May  5 18:28:58 2021

@author: ringel
"""
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from prosi3d.meta.eos.eosPreprocess import EosPreprocess

class EosVisualization():

    def eosprintInfo(layer):
        f = "eosprint_layer" + str(layer).zfill(5) + ".h5"
        df = pd.read_hdf(f, 'df')
        print(df.groupby('exposureType').count())

    def describeLayer(layer):
        '''
        Some statistics about specific layer.
        
        Args: layer
        '''
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
        
        df_laser['cum-sum'] = df_laser['time'].cumsum()
        df_jump['cum-sum'] = df_jump['time'].cumsum()
        
        # Max cumsum of total layer time equals cumsum of only laser times -> strange.
        # but total time with grabXY() equals with sum of laser plus jump times
        print(df.describe())
        
        # some laser vectors are zero length. makes no sense
        print(df_laser[df_laser['dis'] == 0].describe())
        print(df_jump.describe())
        print(df_laser.describe())
        print('Laser: ' + str(df_laser['dis'].max()) + ' mm. Jump: ' + str(df_jump['dis'].max()) + ' mm.')
        print('Laser: ' + str(df_laser['cum-sum'].max()) + ' s. Jump: ' + str(df_jump['cum-sum'].max()) + ' s.')
        print('Anzahl Laser-Vektoren: ' + str(len(df_laser)))
        
        
        #dfout.loc[dfout.exposureType == 0, 'dis'].describe()
        #return df_laser

    def __setColor(expType):
        '''
        defines colors regarding eos exposureType number.
        called by function pfeile().
        
        Args: expType
        '''
        switch={
                # hatch
                0:'dodgerblue',# Ansicht EOSprint
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
        
    def __pfeile(lay,pdf=0,color_vector=0,jumps=0):
        '''
        generates graphical representation of eosprint makro scan vectors either via qt5 or saved as pdf
        jumps = 1 swaps order to show jumps
        pdf = 1 saves pdf instead of qt5 direct plot
        color_vector = >123< colors vector 123
        calls function setColor()
        
        Args: lay,pdf=0,color_vector=0,jumps=0
        Returns: <none>
        '''
        if pdf == 0:
            matplotlib.use('Qt5Agg')
        else:
            matplotlib.use('pdf')
        # part specific colors. vector specific colors - anpassen. sprünge andersfarbig als teile
        # dont use second lines. sometimes directlly following vectors occure --> skywriting when following vector tuple equals?
        f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
        df = pd.read_hdf(f, 'df')
        
        df.reset_index(drop=True, inplace=True)
        #print(df.head(4))
        #print(df.tail(4))
        
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
                    col = EosVisualization.__setColor(df.iloc[i,2])
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
            
    def pfeile2(lay,pdf=0,color_vector=0,jumps=0):
        '''
        edit to show expType=0 too
        generates graphical representation of eosprint makro scan vectors either via qt5 or saved as pdf
        jumps = 1 swaps order to show jumps
        pdf = 1 saves pdf instead of qt5 direct plot
        color_vector = >123< colors vector 123
        calls function setColor()
        
        Args: lay,pdf=0,color_vector=0,jumps=0
        Returns: <none>
        '''
        if pdf == 0:
            matplotlib.use('Qt5Agg')
        else:
            matplotlib.use('pdf')
        # part specific colors. vector specific colors - anpassen. sprünge andersfarbig als teile
        # dont use second lines. sometimes directlly following vectors occure --> skywriting when following vector tuple equals?
        f = "eosprint_layer" + str(lay).zfill(5) + ".h5"
        df = pd.read_hdf(f, 'df')
        
        df.reset_index(drop=True, inplace=True)
        #print(df.head(4))
        #print(df.tail(4))
        
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
        if jumps == 1:# and color_vector != 0:
            color_vector = color_vector*2+1
        
        for i, row in df.iterrows():
            if i%2 == a:
                if color_vector == i:# and color_vector != 0:
                    col = 'crimson'
                else:
                    col = EosVisualization.__setColor(df.iloc[i,2])
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



    def vectorGraph(layer, wind=0):
        '''
        generates chart with ttl signal and square-signal of eosprintapi exported compared to vectortimes calculated data
        wind = [0 .. 100] % from smaller area starting from zero
        
        use for controlling corrections for e.g. skywriting used for calculation of laser-xy-time-signal in vectortimes
        reads processed eosprint-timeline from vectortimes
        reads ttl signal and time from hdf5 starting with end of layer. (see trigger signal for laser-off)
        
        Args: layer, wind=0
        '''
        f = "vectortimes" + str(layer).zfill(5) + ".h5"
        g = "ch4raw_" + str(layer).zfill(5) + ".h5"
        df = pd.read_hdf(f, 'df')
        dg = pd.read_hdf(g, 'df')
        # find first ttl-value greater 1 which equals first laser-on
        laser_on = dg.ttl[(dg.ttl >= 1)].index[0] - dg.index[0]
        # change time-column to seconds
        dg['time'] = pd.to_timedelta(dg['time'])
        dg['time'] = dg.time - (dg.time.iloc[laser_on])
        dg['time'] = dg.time.dt.total_seconds()
        # drop lines before first laser on / recoating
        dg = dg[laser_on:-1]
        # reset index for correct iloc later
        df = df.reset_index(drop=True)
        # set new alternating 0,1,0,1,0,.. column for square wave plot and fill new column
        hi_lo = [0, 1]
        df['hi_lo'] = np.tile(hi_lo, len(df) // len(hi_lo)).tolist() + hi_lo[:len(df)%len(hi_lo)]
        # set up figure
        plt.figure(figsize=(18,6))
        ax = plt.axes()
        #plt.xlim(0, df.iloc[-1,1])
        plt.ylim(-4, 5)
        plt.plot
        #plt.ylim(-0.2, 1.2)
        # iterate all lines and draw arrows (same procedure like in pfeile() for scanvector vizualisation)
        for i, row in df.iterrows():
            if df.iloc[i,1] != df.iloc[i+1,1]:
                if i%2 == 0:
                    col = 'green'
                    vert = 1
                else:
                    col = 'red'
                    vert = -1
                j = i + 1
                # draw horizontal line
                # x, y, dx, dy -> (x, y) to (x+dx, y+dy)
                vec = [df.iloc[i,1], df.iloc[i,5], df.iloc[j,1]-df.iloc[i,1], 0]
                ax.arrow(*vec, width=0.01, head_width=0.0, head_length=0.0, color=col)
                # draw vertical lines
                vec = [df.iloc[i,1], df.iloc[i,5], 0, vert]
                ax.arrow(*vec, width=0.000001, head_width=0.0, head_length=0.0, color='grey')
                # end with last pair
            if i + 1 == len(df) -2:
            #if i + 1 == 200:
                break
            if wind != 0:
                stop = round(wind/100*len(df))
                if i == stop:
                    break
        # add ttl signal
        if wind != 0:
            stop = round(wind/100*len(dg))
            plt.plot(dg.time[:stop], dg.ttl[:stop])
        else:
            plt.plot(dg.time, dg.ttl)#, linewidth=0.1)
        plt.tight_layout()

    def batchPfeile(total):
        '''
        Batch processing for pfeile()
        argument: total layer number for processing starting with 1
        
        Args: total
        '''
        lay = 1
        while lay <= total:
            EosVisualization.__pfeile(lay,1)
            lay += 1
            
    def jumpHist(layer, bins=20, precision=6, swap=0, cnt_only=0):
        '''
        Plot Histogram to check if calculated jumptimes (eos print export) equal measured ones from ttl signal.
        Use presicion for grouping by decimal places (round) and bins for number of bars to draw.
        Swap changes to represent lasertimes.
        
        Args: layer, bins=20, precision=6, swap=0, cnt_only=0
        Returns: Histogram-plot
        '''
        #global ttl_jump, ttl_laser, eos_jump, eos_laser, ttl, eos
        ttl_jump, ttl_laser = tJumpTTL(layer)
        # one layer, debugmode = 2, read only
        eos_jump, eos_laser = EosPreprocess.vecTiming_hdf(layer,layer,2,0)
        nulljumps = (eos_laser.time == 0).sum()
        print('Count EOSP - TTL:')
        print(len(eos_laser) - len(ttl_laser))
        print('Jumps with length zero')
        print(nulljumps)
        print('not visible in TTL signal: ')
        print(len(eos_laser) - len(ttl_laser) - nulljumps)
        
        # show laser vectors instead of jumps
        if swap == 1:
            ttl_jump['t_round'] = round(ttl_jump.diff_ms/1000, precision)
            eos_jump['t_round'] = round(eos_jump.time, precision)
            
            ttl = ttl_jump.t_round.value_counts().nlargest(bins)
            eos = eos_jump.t_round.loc[eos_jump.t_round != 0].value_counts().nlargest(bins)
            
        else:
            ttl_laser['t_round'] = round(ttl_laser.diff_ms/1000, precision)
            eos_laser['t_round'] = round(eos_laser.time, precision)
            
            ttl = ttl_laser.t_round.value_counts().nlargest(bins)
            eos = eos_laser.t_round.loc[eos_laser.t_round != 0].value_counts().nlargest(bins)
        
        
        #print(str(len(ttl)) + ' found with entered presicion.')
        print('_____ Note that nlargest are plotted (correspinding to bins and precision) _____')
        print('TTL: ' + str(ttl.sum()) + ' of ' + str(len(ttl_laser)) + ' displayed')
        print('EOS: ' + str(eos.sum()) + ' of ' + str(len(eos_laser) - nulljumps) + ' displayed')
        
        if cnt_only==0:
            plt.figure(figsize=(18,6))
            plt.tight_layout()
            ax = plt.subplot(111)
            ax.set_yscale('log')
            ax.set_xlabel('vector length [s]')
            ax.set_ylabel('count')
            ax.bar(ttl.index, ttl, width=0.00003, color='b', align='center')
            ax.bar(eos.index, eos, width=0.00002, color='r', align='center')
            ax.legend(['ttl','eos'])
            plt.show()
        
    def compareJumps(layer):
        '''
        Compare measured jumps from ttl with eosprint data and match measured times to jumplength
        Goal is to have a comparation table / dictionary. Could have more features like previous and following speed or position/radii out of center
        
        Remaining issue:
            Not all eosprint vectors are measured in ttl @ 50 kHz
            
        
        Args: Layernumber calls tJumpTTL() and vecTiming_hdf()
        Retrn: target
        '''
        global ttl_jump, ttl_laser, eos_jump, eos_laser, target, dbase, ttl, eos2
        global shortys
        # read data
        ttl_jump, ttl_laser = tJumpTTL(layer)
        print('Previous inter-layer time:')
        print(ttl_laser['diff_ms'].iloc[0])
        
        # one layer, debugmode = 2, read only
        eos_jump, eos_laser = EosPreprocess.vecTiming_hdf(layer,layer,2,0)
        
        
        
        # First line is layer change
        ttl = ttl_laser.iloc[1:,:]
        # ignore zero jumps
        eos = eos_laser.loc[(eos_laser.dis != 0)]
        
        eos.loc[(np.abs(eos.dphi) < 181) & (np.abs(eos.dphi) > 179), 'sky10'] = 1
        eos.loc[eos.sky10 != 1, 'sky10'] = 0
        
        print('difference of measured and provided jumps:')
        cnt_error = len(eos) - len(ttl)
        print(cnt_error)
        # shortys = eos_jump.loc[eos_jump.time < 0.00001]
        # exclude contours or better where no zerojumps before/after
        zeroj_idx = eos_laser.loc[eos_laser.dis == 0].index
        zeroj_idx1 = zeroj_idx + 1
        if zeroj_idx1[-1] > eos_laser.index[-1]:
            zeroj_idx1 = zeroj_idx1[0:-1]
        zeroj_idx2 = zeroj_idx - 1
        a=np.array(zeroj_idx1)
        b=np.array(zeroj_idx2)
        c = np.unique(np.concatenate((a,b),0))
        
        eos_zerojidx = eos_jump.drop(c)
        
        shortys = eos_zerojidx.time.nsmallest(cnt_error)
        print('temporal longest shorty:')
        print(shortys.max())
        print('Laservectors <shortys> with temporal length < 10 us found:')
        print(eos_jump.time.loc[eos_jump.time < 0.00001].value_counts().describe()['count'])
        
        
        # in that way found shortys is wrong. contours are found and before/after zero jumps are not in "eos" anymore
        eos.loc[shortys.index-1] = eos.loc[shortys.index-1] + eos.loc[shortys.index+1]
        # set skywriting to 999 to find those not usable jumps later after resetting index
        eos.loc[shortys.index-1].sky10 = 999
        eos2 = eos.drop(shortys.index+1)
        # workaround to get equal length --> error
        #eos2 = eos.drop(eos.dis.nsmallest(len(eos) - len(ttl)).index)
        # Zeit
        
        #eos.reset_index(drop=True, inplace=True)
        eos2.reset_index(drop=True, inplace=True)
        ttl.reset_index(drop=True, inplace=True)
        
        dbase = pd.DataFrame({'dis_eos': eos2.dis, 'time_ttl': ttl.diff_ms, 'sky': eos2.sky10})
        dbase['time_ttl'] = dbase['time_ttl']/1000
        # merge doesnt work with duplicates in "dict"
        dbase = dbase.drop_duplicates(subset=['dis_eos', 'sky'])
        
        # target_init is new dataset which needs time values from dict / dbase
        target_init = pd.DataFrame({'dis_eos': eos.dis, 'sky': eos.sky10})
        target = target_init.merge(dbase, how='left')
        
        dbase['v_mean'] = dbase.dis_eos/dbase.time_ttl
        
        f = "jump_data" + str(layer).zfill(5) + ".h5"
        dbase.to_hdf(f, key='dbase', mode='w')
        
        # if nan values use lin interpolation
        #    dbase_sort = dbase.sort_values(by=['dis_eos', 'time_ttl'])
        #    interpol = interp1d(dbase_sort.dis_eos, dbase_sort.time_ttl, bounds_error=False)
        #    target_init['time_ttl'] = interpol(target_init.dis_eos)
        #    target.time_ttl.loc[target.time_ttl.isna()] = target_init.time_ttl.loc[target.time_ttl.isna()]
        
        return target