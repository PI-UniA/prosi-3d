import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
import tqdm
import pandas as pd
import prosi3d.eos.vector
import logging
import inspect



def vectorGraph(path, layer, ub=0, lb=0, corr=0):
    """
    Helper function for generating chart with ttl signal and square-signal of eosprintapi exported eoslaserpath
    Use upper bound (ub) and lower bound (lb) for specific chart windows. The full-frame needs some CPU time.
    Use corr!=0 if the ttl number needs an offset to the entered layer (number of eoslaserpath-file).

    Use for controlling corrections for e.g. skywriting used for calculation of laser-xy-time-signal in vectortimes
    Reads processed eosprint-timeline from vectortimes
    Reads ttl signal and time from hdf5 starting with the end of the layer. (see trigger signal for laser-off)

    Calls vector.folder2Files()

    Issue: first laser vector is graphically not represented

    Args:
        path (str): Path of the input hdf5 files directory
        layer (int): Number of the layer
        ub (int, optional): Upper boundary value, must be between 0 and 100, defaults to 0
        lb (int, optional): Lower boundary value, must be between 0 and 100, defaults to 0
        corr (int, optional): Correction value, defaults to 0
    Returns:
        1
    """
    corr = int(corr)
    if lb > ub:
        print("lower boundary value (lb) must be smaller then upper boundary value (ub). Values are flipped.")
        flip = ub
        ub = lb
        lb = flip
    if ub > 100 or lb > 100 or ub < 0 or lb < 0:
        print("ub and lb must be between 0 and 100. lb is set to 0 and ub to 5.")
        ub = 5
        lb = 0

    _, _, _, vecdir, ttldir, _, _ = prosi3d.eos.vector.folder2Files(path, 0)

    f = vecdir + "\\eoslaserpath_" + str(layer).zfill(5) + ".h5"
    g = ttldir + "\\ch4raw_" + str(layer + corr).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    dg = pd.read_hdf(g, 'df')

    dg.columns = ['time', 'lse', 'ttl', 'kse_bp', 'kse_rec']
    # find first ttl-value greater 1 which equals first laser-on
    laser_on = dg.ttl[(dg.ttl >= 1)].index[0] - dg.index[0]

    if dg['time'].dtype != 'float64':
        dg['time'] = dg['time'].values.astype('datetime64[ns]')
    dg['time'] = dg.time - (dg.time.iloc[laser_on])
    if dg['time'].dtype != 'float64':
        dg['time'] = dg.time.dt.total_seconds()

    # drop lines before first laser on / recoating
    dg = dg[laser_on:-1]
    # reset index for correct iloc later
    df = df.reset_index(drop=True)
    # set new alternating 0,1,0,1,0,.. column for square wave plot and fill new column
    hi_lo = [0, 1]
    df['hi_lo'] = np.tile(hi_lo, len(df) // len(hi_lo)).tolist() + hi_lo[:len(df) % len(hi_lo)]
    # set up figure
    plt.figure(figsize=(18, 6))
    ax = plt.axes()
    plt.ylim(-4, 5)
    plt.plot
    # iterate all lines and draw arrows (same procedure like in genVectors() for scanvector vizualisation)
    start = round(lb / 100 * len(df))
    stop = round(ub / 100 * len(df))
    for i, row in df.iterrows():
        if lb != 0:
            if i < start:
                continue
        if df.loc[i, 'cum_sum'] != df.loc[i + 1, 'cum_sum']:
            if i % 2 == 0:
                col = 'green'
                vert = 1
            else:
                col = 'red'
                vert = -1
            j = i + 1
            # draw horizontal line
            # x, y, dx, dy -> (x, y) to (x+dx, y+dy)
            vec = [df.loc[i, 'cum_sum'], df.loc[i, 'hi_lo'], df.loc[j, 'cum_sum'] - df.loc[i, 'cum_sum'], 0]
            ax.arrow(*vec, width=0.01, head_width=0.0, head_length=0.0, color=col)
            # draw vertical lines
            vec = [df.loc[i, 'cum_sum'], df.loc[i, 'hi_lo'], 0, vert]
            ax.arrow(*vec, width=0.000001, head_width=0.0, head_length=0.0, color='grey')
            # end with last pair
        if i + 1 == len(df) - 2:
            break
        if ub != 0:
            if i == stop:
                break

    # add ttl signal
    # plot x axis from zero to upper boundary
    if ub != 0 and lb == 0:
        stop = round(ub / 100 * len(dg))
        plt.plot(dg.time[:stop], dg.ttl[:stop])
    if ub == 0 and lb != 0:
        start = round(lb / 100 * len(dg))
        plt.plot(dg.time[start:], dg.ttl[start:])
    if ub != 0 and lb != 0:
        start = round(lb / 100 * len(dg))
        stop = round(ub / 100 * len(dg))
        plt.plot(dg.time[start:stop], dg.ttl[start:stop])
    # full x axis plot
    if ub == 0 and lb == 0:
        plt.plot(dg.time, dg.ttl)  # , linewidth=0.1)
    plt.tight_layout()
    return 1

def eosprintInfo(path, layer, vers=1):
    """
    Helper function to print counted exposureTypes in vers=0: eosprint_layer or vers=1: eoslaserpath
    Note that contours in EOSPRINT API 2.8 exports (eosprint_layer) are defined wrong as infill (2), which is corrected in eoslaserpath.
    Calls vector.folder2Files()

    Args:
        path (str): Path of the input hdf5 files directory
        layer (int): Number of the layer
        vers (int,optional): Decides which eos files will be processed, defaults to 1
    Returns:
        1
    """

    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    logger.info(out)

    _, _, _, vecdir, _, _, _ = prosi3d.eos.vector.folder2Files(path, 0)
    if vers == 0:
        f = vecdir + '\\' + "eosprint_layer" + str(layer).zfill(5) + ".h5"
    if vers == 1:
        f = vecdir + '\\' + "eoslaserpath_" + str(layer).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    logger.info(df.groupby('exposureType').count())
    return 1

def plotTTL(path, layer, ub=0, lb=0, corr=0):
    """
    Helper function for generating chart with ttl signal and square-signal of eosprintapi exported eoslaserpath
    Use upper bound (ub) and lb for specific chart window.The full-frame needs some CPU time.
    Use corr!=0 if ttl number needs an offset to entered layer (number of eoslaserpath-file).

    Use for controlling corrections for e.g. skywriting used for calculation of laser-xy-time-signal in vectortimes
    Reads processed eosprint-timeline from vectortimes
    Reads ttl signal and time from hdf5 starting with the end of the layer. (see trigger signal for laser-off)

    Calls vector.folder2Files()

    Issue: first laser vector is graphically not represented

    Args:
        path (str): Path of the input hdf5 files directory
        layer (int): Number of the layer
        ub (int, optional): Upper boundary value, must be between 0 and 100, defaults to 0
        lb (int, optional): Lower boundary value, must be between 0 and 100, defaults to 0
        corr (int, optional): Correction value, defaults to 0
    Returns:
        1
    """

    # avoid errors by false arguments
    corr = int(corr)
    if lb > ub:
        print("lower boundary value (lb) must be smaller then upper boundary value (ub). Values are flipped.")
        flip = ub
        ub = lb
        lb = flip
    if ub > 100 or lb > 100 or ub < 0 or lb < 0:
        print("ub and lb must be between 0 and 100. lb is set to 0 and ub to 5.")
        ub = 5
        lb = 0

    _, _, _, vecdir, ttldir, _, _ = prosi3d.eos.vector.folder2Files(path, 0)

    g = ttldir + "\\ch4raw_" + str(layer + corr).zfill(5) + ".h5"
    dg = pd.read_hdf(g, 'df')

    dg.columns = ['time', 'lse', 'ttl', 'kse_bp', 'kse_rec']
    # find first ttl-value greater 1 which equals first laser-on
    laser_on = dg.ttl[(dg.ttl >= 1)].index[0] - dg.index[0]

    # change time-column to seconds
    if dg['time'].dtype != 'float64':
        dg['time'] = dg['time'].values.astype('datetime64[ns]')
    dg['time'] = dg.time - (dg.time.iloc[laser_on])
    if dg['time'].dtype != 'float64':
        dg['time'] = dg.time.dt.total_seconds()

    # set up figure
    plt.figure(figsize=(18, 6))
    # plt.xlim(0, df.iloc[-1,1])
    plt.ylim(-4, 5)
    plt.plot

    # add ttl signal
    # plot x axis from zero to upper boundary
    if ub != 0 and lb == 0:
        stop = round(ub / 100 * len(dg))
        plt.plot(dg.time[:stop], dg.ttl[:stop])
    if ub == 0 and lb != 0:
        start = round(lb / 100 * len(dg))
        plt.plot(dg.time[start:], dg.ttl[start:])
    if ub != 0 and lb != 0:
        start = round(lb / 100 * len(dg))
        stop = round(ub / 100 * len(dg))
        plt.plot(dg.time[start:stop], dg.ttl[start:stop])
    # full x axis plot
    if ub == 0 and lb == 0:
        plt.plot(dg.time, dg.ttl)  # , linewidth=0.1)
    plt.tight_layout()
    return 1

def loopVectors(path, mode=0):
    """
    Batch processing for genVectors()
    Start loop with either single layer number, laser paths or both
    Calls genVectors() and vector.folder2Files()
    Saves graphical representation as pdf files
    mode=1: only eosprint_layer
    mode=2: only eoslaserpath
    mode=0: both

    Args:
        path (str): Path of the input hdf5 files directory
        mode (int, optional): Decides which eos files will be processed, defaults to 0
    Returns:
        1
    """

    _, _, _, vecdir, _, _, _ = prosi3d.eos.vector.folder2Files(path, 0)

    pdfdir = path + '\\pdf'
    try:
        os.mkdir(pdfdir)
    except:
        pass

    eoslayers = []
    num = -1
    # all files in vecdir
    eosfiles = [f.path for f in os.scandir(vecdir)]
    for item in eosfiles:
        # check if h5 file
        if item.rsplit('.', 1)[-1] == 'h5':
            # check if 'eosprint_layer'
            fname = item.rsplit('\\', 1)[-1]
            if 'eosprint_layer' in fname and mode != 2:
                try:
                    num = fname[14:19]
                    lay = int(num)
                except:
                    pass
            if 'eoslaserpath_' in fname and mode != 1:
                try:
                    num = fname[13:18]
                    lay = int(num)
                except:
                    pass
            if num == str(lay).zfill(5):
                eoslayers.append(item)
        num = -1

    for item in tqdm(eoslayers):
        try:
            genVectors(item, pdf=1)
        except:
            print(f"ERROR in loopVectors: {item} could not be processed. Check manually!")
        lay += 1

    return 1


def genVectors(lay, path=None, pdf=0, color_vector=0, jumps=0):
    """
    Generates graphical representation of eosprint makro scan vectors either via qt5 or saved as pdf (pdf=1 saves pdf instead of qt5 inline plot)
    jumps = 1 swaps order to show jumps
    color_vector = >123< colors vector number 123
    Calls function setColor() and vector.folder2Files()
    Give it either a layer number with the project path or a direct filepath

    Args:
        lay (int or str): Layer number or direct filepath
        path (str, optional): Path of the input hdf5 files directory, defaults to None
        pdf (int, optional): Decides how the graphical representation will be shown, defaults to 0
        color_vector (int, optional): Vector number will be highlighted in the graphical representation, defaults to 0
        jumps (int, optional): Amount to skip between vectors, defaults to 0
    Returns:
        1
    """

    if pdf == 0:
        matplotlib.use('Qt5Agg')
    else:
        matplotlib.use('pdf')
    # part specific colors. vector specific colors - anpassen. sprünge andersfarbig als teile
    # dont use second lines. sometimes directlly following vectors occure --> skywriting when following vector tuple equals?

    # check if file or layer number
    try:
        num = int(lay)
        if lay == num:
            if path is None:
                print('Layer number entered but no project directory/path')
            else:
                _, _, _, vecdir, _, _, _ = prosi3d.eos.vector.folder2Files(path, 0)
                f = vecdir + '\\' + "eosprint_layer" + str(lay).zfill(5) + ".h5"
    except:
        # true if it is a file -> then it should be the direct file for processing
        if os.path.isfile(lay):
            f = lay

    df = pd.read_hdf(f, 'df')

    df.reset_index(drop=True, inplace=True)

    # size definition for plotting in inches
    plt.figure(figsize=(96, 96))
    ax = plt.axes()
    ax.set_aspect('equal')
    plt.xlim(0, 250)
    plt.ylim(0, 250)

    # first layer has odd line number count
    # odd line numbers: skip first line (index 0) and use then following pairs
    if len(df) % 2 == 1:
        a = 1
        if jumps == 1:
            a = 0
    # even line numbers: use following pairs starting with first line
    else:
        a = 0
        if jumps == 1:
            a = 1
    if jumps == 1 and color_vector != 0:
        color_vector = color_vector * 2 + 1

    for i, row in df.iterrows():
        if i % 2 == a:
            if color_vector != 0 and color_vector == i:
                col = 'crimson'
            else:
                col = setColor(df.iloc[i, 2])
            j = i + 1
            vec = [df.iloc[i, 0], df.iloc[i, 1], df.iloc[j, 0] - df.iloc[i, 0], df.iloc[j, 1] - df.iloc[i, 1]]
            ax.arrow(*vec, head_width=0.05, head_length=0.1, color=col)
        if i + 1 == len(df) - 1:
            break
    if pdf == 1:
        # without file ending
        fname = f.rsplit('.', 1)[0]
        # other folder
        fname = fname.replace('\\vec\\', '\\pdf\\')
        plt.savefig(fname + '.pdf', format='pdf', dpi=600)
        plt.close()
        del (df)
        matplotlib.use('Qt5Agg')
    return 1

def setColor(expType):
    """
    Defines colors regarding eos exposureType number.
    Called by function genVectors().

    Args:
        expType (int): exposure type
    Returns:
        (str): Color according to expType or black Color if the expType is invalid
    """
    switch = {
        # hatch
        0: 'dodgerblue',  # View of part outter edge EOSprint
        # darker -> downskin, brigther -> upskin
        1: 'seagreen',  # down
        2: 'mediumspringgreen',  # in
        3: 'springgreen',  # up
        # contour
        4: 'darkviolet',  # down
        5: 'mediumorchid',  # in
        6: 'magenta',  # up
        10: 'violet',
        # edge
        7: 'orangered',
        # support
        8: 'dodgerblue',
        # jump
        9: 'darkorange',
        11: 'darkorange'
    }
    return switch.get(expType, 'black')

