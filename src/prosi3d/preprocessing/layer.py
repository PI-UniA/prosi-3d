from scipy.signal import savgol_filter
import pandas as pd
import numpy as np
from tqdm import tqdm

def loopLayerMatchList(path, matchlist, partlist, layer_partids, what='ttldir', correction=0):
    eostxtfile, paramfile, jobfile, vecdir, ttldir, resdir, logdir, _ = folder2Files(path, 0)

    polygons = getPolygons(path, partlist)
    
    # get ttl files list
    files = filesInFolder_simple(locals()[what], 'h5')

    checks = []
    for item in files:
        item = item.rsplit('_')[-1]
        item = item.rsplit('.', 1)[0]
        try:
            num = int(item)
        except:
            continue
        if item == str(num).zfill(5):
            checks.append(num)

    checks = np.array(checks)
    matchlist = np.array(matchlist)+correction

    matches = checks[np.isin(checks,matchlist)]

    for lay in matches:
        print(f'run function for: {lay}')
        file = path + '\\res\\eosxytime_' + str(lay+correction).zfill(5) + ".h5"
        # deconstruct string to np array of int
        partids = layer_partids.loc[lay, 'partIds']
        for item in ['[', ',', ']', "'"]:
            partids = partids.replace(item, '')
        partids = np.fromstring(partids, dtype=int, sep=' ').astype(int)

        labelLayer_bindingError(file, partids, polygons)
            # open xytime for lay
            # filter partId which has failure end / first true layer
            # ask all resulting points if in polygon
    
    return matches


def labelLayer_bindingError(file, partids, polygons):
    '''
    open xytime for lay
    filter partId which has failure end / first true layer
    ask all resulting points if in polygon
    '''
    xyt = pd.read_hdf(file, 'df')

    xyt['binding_error1'] = 0
    # xyt.loc[xyt['time'] >= 0]['binding_error1'] = 0
    xyt['partId'] = xyt['partId'].astype(int)

    print(f'File opened: {file}')
    # iterate samples for matching part IDs    
    for row in xyt[{'x_mm', 'y_mm'}].loc[xyt['partId'].isin(partids)].itertuples():
        polygon = polygons.loc(row.Index)
        if point_in_polygon(polygon, (row.x_mm, row.y_mm)):
            # set label if point in polygon returns true
            xyt.loc[row.Index, 'binding_error1'] = 1
    
    xyt.to_hdf(file, 'df')

def errorLayer(folder_stl):
    '''
    Calculate all first layers above missing layers and return sorted list without duplicates
    '''
    # get all files in folder
    files = filesInFolder_simple(folder_stl, 'txt')
    # drop duplicates ignoring last seperator like '_' for numbering
    files = dropFileDuplicates(files, sep='_')

    layers = []
    # stl base name without duplicate number
    base_name = []
    # correlating missing layers
    base_layers =  []
    for file in files:
        # get height by file name of main variant
        layer = file.rsplit('_', 1)[-1].rsplit('x')[0].split('+')
        layer = sum([int(item) for item in layer]) + 1
        layers.append(layer)

        # following layers of this part
        # file name is already reduced to main variant
        
        ftxt = folder_stl + '\\' + file + '_0.txt'
        zduplicate_layers = prosi.getZ(ftxt)
        layers = layers + zduplicate_layers

        zduplicate_layers.append(layer)
        base_name.append(file)
        base_layers.append(zduplicate_layers)

    layers = list(dict.fromkeys(layers))
    layers.sort()
    
    base_and_layers = pd.DataFrame()
    base_and_layers['base'] = base_name
    base_and_layers['layers'] = base_layers



    return layers, base_and_layers

def reshapeLayerPartIds(error_layers, base_and_layers, partlist):
    '''
    create an array with layers above each error and relevant partIds within that layers
    
    '''
    ## shape list of error layers to "lay: stl basenames"
    layer_prt_names = pd.DataFrame(error_layers)
    layer_prt_names.columns = ['lay']
    layer_prt_names.set_index('lay', inplace=True)
    layer_prt_names['stl_base_names'] = ''
    for lay in error_layers:
        for idx, layers in base_and_layers.layers.items():
            if np.isin(lay, layers):
                stl_base = layer_prt_names.loc[lay, 'stl_base_names'] + base_and_layers.loc[idx, 'base'] + ', '
                layer_prt_names.loc[lay, 'stl_base_names'] = stl_base
    
    ## stl basenames from openjob file
    partlist = [name.rsplit('_', 1)[0] for name in partlist]
    partlist = pd.Series(partlist)
    partlist.index += 1

    ## find base name specific partIds as strings and delete line breaks
    base_and_layers['partIds'] = ''
    for idx, base in base_and_layers.base.items():
        repl = str(partlist.loc[partlist == base].index.values.astype(str))
        repl = repl.replace('\n', '')
        base_and_layers['partIds'].loc[idx] = repl

    ## replace stl base names with partIds in layer list
    # THIS IS REALLY IMPORTANT: THE PLUS CHARACTER NEEDS TO BE EXCHANGED WITHIN THE DICTIONARY
    base_and_layers['base'] = base_and_layers['base'].str.replace('\+', '\\+', regex=True)
    #base_ids_dict = dict(zip(base_and_layers['base'], base_and_layers['partIds']))

    base_ids_dict = pd.Series(base_and_layers['partIds'].values,index=base_and_layers['base']).to_dict()
    layer_prt_names['partIds'] = layer_prt_names['stl_base_names'].replace(base_ids_dict, regex=True)

    # alternatives to replace by dict:
    # for old, new in base_ids_dict.items():
    #     layer_prt_names['partIds'] = layer_prt_names['stl_base_names'].str.replace(old, new, regex=True)
    # for row in base_and_layers[{'base', 'partIds'}].itertuples():
    #     layer_prt_names['partIds'] = layer_prt_names['stl_base_names'].str.replace(row.base, row.partIds, regex=True)

    ## now we have a dataframe with index=lay == layers above each error and relevant partIds in that layer
    return layer_prt_names

def correctLayChange(path, files=[]):
    '''
    Finds layerchanges by unique "laser-off" signal using savitzky-golay-filter and its increase dx
    If 1500 values are inside boarders then layerchange is found.
    resulting time delay is 0,03 s beyond laser off
    
    TODO: add pausing for 50000 values before next trigger is allowed (peaks in rawsignal sometimes cause double triggering)
    
    Args: time, signal
    Returns: times, lines
    '''

    # if no list is given then process all files in folder
    if files==[]:
        # files without check for file name syntax
        files = filesInFolder_simple(path, typ='h5')
    
    if len(files) == 0:
        print('No files are given!')
        return
    
    for file in tqdm(files):
        timeline = pd.read_hdf(file, 'df')

        # # Filter doesnt work if there are zeros or infinity values
        # timeline.time.dropna(inplace=True)
        # timeline.ttl.dropna(inplace=True)
    
        #global laserdx
        x_fil = savgol_filter(timeline.ttl, 999, 2)
        x_fil = pd.Series(x_fil)
        laserdx = x_fil.diff(periods=1)
        print(type(laserdx))
        
        lbound = 0.000001
        ubound = 0.005
        n = 1500
        

        # sampling width
        ts = timeline.time.diff().median()
        # convert to int for comparison with index
        min_dist = int(15 / ts)
        #print(ts, min_dist)

        filter_dx = laserdx.loc[(laserdx <= ubound) & (laserdx >= lbound)]

        changes = []
        i = 0
        changeidx = -min_dist
        idx0 = filter_dx.index[0]
        for idx in filter_dx.index:
            # only if distance is given
            if idx > (changeidx + min_dist):
                if idx == idx0 + 1:
                    i += 1

                    if i == n:
                        changeidx = idx - n - 1
                        print(f'layerchange at index {changeidx}')
                        changes.append(changeidx)
                        i = 0
                        
                else:
                    i = 0
                idx0 = idx
        
        # split dataframe
        cnt = len(changes)
        n = 0
        if cnt > 2:
            f1, f2 = file.rsplit('.', 1)
            for idx in changes[0:-1]:
                
                fnew = f1 + '_' + str(n) + '.' + f2
                n += 1
                if n == cnt - 1:
                    # last layer
                    timeline.iloc[idx:,:].to_hdf(fnew, key='df', mode='w')
                else:
                    timeline.iloc[idx:changes[n],:].to_hdf(fnew, key='df', mode='w')

def reshape_eos_layer_file(eos_layer_file):
    '''
    Reshapes dataset where two lines represent one weld into a "one line represents one weld" shape
    Args: eos_layer_file
    Returns: eos_layer
    '''
    # not really necessary anymore, since all datasets should now be even in length (15.11.2022)
    if len(eos_layer_file)%2 == 1:
        starts = eos_layer_file.iloc[1::2].copy()
        ends = eos_layer_file.iloc[2::2].copy()
    else:
        starts = eos_layer_file.iloc[0::2].copy()
        ends = eos_layer_file.iloc[1::2].copy()
    
    ## altenatively drop first row
    # if len(eos_layer_file)%2 == 1:
    #     eos_layer_file2 = eos_layer_file.drop(eos_layer_file.index[0])
    # starts = eos_layer_file2.iloc[0::2].copy()
    # ends = eos_layer_file2.iloc[1::2].copy()
    
    starts.columns = ['x0_mm', 'y0_mm', 'expType', 'prtId']
    ends.columns = ['x1_mm', 'y1_mm', 'expType', 'prtId']
    starts.reset_index(drop=True, inplace=True)
    ends.reset_index(drop=True, inplace=True)
    # does not work if len mismatch in first layer. check first layer slicing!
    eos_layer = pd.merge(starts, ends, left_index=True, right_index=True)
    # control for correct expType and prtId
    if len(eos_layer.loc[(eos_layer['expType_x'] != eos_layer['expType_y']) & (eos_layer['prtId_x'] != eos_layer['prtId_y'])]) == 0:
        eos_layer.drop(['expType_x', 'prtId_x'], axis='columns', inplace=True)
        eos_layer.columns = ['x0_mm', 'y0_mm', 'x1_mm', 'y1_mm', 'expType', 'prtId']
        print('EOS Layer File successfully reshaped.')
    else:
        print('reshape_eos_layer_file: WARNING: Starts and ends could not be merged.')
    
    return eos_layer

def correctContourExpTypes(eos_layer):
    '''
    correct wrong expType of contours if x1 and y1 equal x0 and y0 of following vectors for expTypes 1, 2, 3
    Nicht korrigierte Upskin downskins könnten der Fehler in den bisherigen versionen gewesen sein! (15.11.2022)

    Args: eos_layer
    Returns: eos_layer
    '''
    eos_layer['x0_next'] = eos_layer['x0_mm'].shift(periods=-1, axis=0, fill_value=-1)
    eos_layer['y0_next'] = eos_layer['y0_mm'].shift(periods=-1, axis=0, fill_value=-1)

    index_downskin_contours = eos_layer.loc[(eos_layer['x1_mm'] == eos_layer['x0_next']) & (eos_layer['y1_mm'] == eos_layer['y0_next']) & (eos_layer.expType == 1)].index
    eos_layer.loc[(index_downskin_contours | index_downskin_contours + 1), 'expType'] = 4
    index_infill_contours = eos_layer.loc[(eos_layer['x1_mm'] == eos_layer['x0_next']) & (eos_layer['y1_mm'] == eos_layer['y0_next']) & (eos_layer.expType == 2)].index
    eos_layer.loc[(index_infill_contours | index_infill_contours + 1), 'expType'] = 5
    index_upskin_contours = eos_layer.loc[(eos_layer['x1_mm'] == eos_layer['x0_next']) & (eos_layer['y1_mm'] == eos_layer['y0_next']) & (eos_layer.expType == 3)].index
    eos_layer.loc[(index_upskin_contours | index_upskin_contours + 1), 'expType'] = 6
    
    print(f'Changed exposures: {len(index_downskin_contours)} (down), {len(index_infill_contours)} (infill), {len(index_upskin_contours)} (up)')
    
    return eos_layer

def assign_weld_speed(path, eos_layer):
    '''
    input path and eos_layer with corrected exposure types --> correctContourExpTypes()
    add welding speeds to each line based on parameter file
    Args: path, eos_layer
    Returns: eos_layer    
    '''
    _, paramfile, _, _, _, _, logdir, _ = prosi.folder2Files(path, 0)
    param = pd.read_csv(paramfile, sep=';')
    param.columns = ['prtId', 'partname', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    # true partid starts counting by 1
    param['prtId'] = param['prtId'] + 1
    parts = eos_layer['prtId'].unique()
    for part in parts:
        # select all exposures for this partid
        exp_types = eos_layer.loc[(eos_layer['prtId'] == part), 'expType'].unique()
        for exptype in exp_types:
            speed = param.loc[(param['prtId'] == part), str(exptype)]
            eos_layer.loc[(eos_layer['expType'] == exptype) & (eos_layer['prtId'] == part), 'speed'] = speed.iloc[0]
    
    return eos_layer


def ttl2Welds(layer, path, tresh1=1, tresh2=-1):
    '''
    New version of tJumpTTL() returning dataframe for ttlweld class.
    ttlweld class equals weld class where one entry represents one weld.
    duration returned is maybe one sampling width too long - (substraction added 28.11.2022)
    16.11.2022

    Args: layer (integer), path, tresh1=1, tresh2=-1
    Returns: lsr_strt_jmp_len_jmp_strt_lsr_len (pandas dataframe)
    '''
    eostxtfile, paramfile, jobfile, vecdir, ttldir, resdir, logdir, _ = prosi.folder2Files(path, 0)

    f = ttldir + "\\ch4raw_" + str(layer).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    df.columns = ['time', 'lse', 'ttl', 'kse_bp', 'kse_rec']
    df = df.drop(['lse', 'kse_bp', 'kse_rec'], axis=1)
    
    # difference of indexes marks laserweld by values greater than one and by that the next jump
    min_len_idx = 1
    # first value above threshold is laser on for the first time
    power = df['ttl'].loc[(df['ttl'] >= tresh1)].index[0]
    # loc gets index, iloc counts places
    # temporal difference between each sample
    df['diffs'] = df['time'].diff()
    # use median of timediffs for sampling time step in ms. 50 kHz = 0.02 ms
    sampling_ms = df['diffs'].median()*1000
    # threshold boarder, empiric value for 50kHz was around row 7000 -> 0.3 s for any sampling frequ
    # corrected to calculate it directly
    #indexboarder = power + int(0.294/sampling_ms*1000)
    power_1s = power + int(1/sampling_ms*1000)
    df_temp = df[power:power_1s].copy()
    indexboarder = df_temp.loc[(df_temp['ttl'] > (tresh1+1.5))].index[-1]
    del df_temp

    # jumps = all values lower then thresholds represent jumps and vice versa for welds
    jumps = df.loc[((df['ttl'] < tresh1) & (df.index < indexboarder)) | ((df['ttl'] < tresh2) & (df.index >= indexboarder))].copy()
    welds = df.loc[((df['ttl'] >= tresh1) & (df.index < indexboarder)) | ((df['ttl'] >= tresh2) & (df.index >= indexboarder))].copy()

    ## JUMPS
    # new column with index integers
    jumps['idx'] = jumps.index
    # values greater 1 in diff_idx are idx-lengths of laserwelds between jumps
    jumps['diff_idx'] = jumps.idx.diff()
    # if difference between indices greater min_len_idx then laser was off for that time
    # rows with start of jump end length of weld before
    jmp_strt_lsr_len = jumps.loc[jumps['diff_idx'] > min_len_idx].copy()

    ## WELDS vice versa
    welds['idx'] = welds.index
    welds['diff_idx'] = welds.idx.diff()
    lsr_strt_jmp_len = welds.loc[welds['diff_idx'] > min_len_idx].copy()

    # calculate temporal length diff_ms using first and last entry 
    jmp_strt_lsr_len['prev_idx'] = jmp_strt_lsr_len.index - jmp_strt_lsr_len['diff_idx']
    jmp_strt_lsr_len['diff_ms'] = (jmp_strt_lsr_len['time'] - df.loc[jmp_strt_lsr_len['prev_idx'], 'time'].values)*1000
    lsr_strt_jmp_len['prev_idx'] = lsr_strt_jmp_len.index - lsr_strt_jmp_len['diff_idx']
    lsr_strt_jmp_len['diff_ms'] = (lsr_strt_jmp_len['time'] - df.loc[lsr_strt_jmp_len['prev_idx'], 'time'].values)*1000

    # timelaser in lsr_strt_jmp_len gives timeval for laservector start (high ramp) --> use for synchronization with eos data
    jmp_strt_lsr_len['exp_time'] = jmp_strt_lsr_len['time'] - df.loc[power, 'time']
    lsr_strt_jmp_len['exp_time'] = lsr_strt_jmp_len['time'] - df.loc[power, 'time']

    jmp_strt_lsr_len.drop(['ttl', 'diffs', 'idx', 'prev_idx', 'diffs'], axis='columns', inplace=True)
    lsr_strt_jmp_len.drop(['ttl', 'diffs', 'idx', 'prev_idx', 'diffs'], axis='columns', inplace=True)
    
    ## shift to have laser weld start, length as well as following jump start and length in the exact same row
    jmp_strt_lsr_len.reset_index(drop=False, inplace=True)
    lsr_strt_jmp_len.reset_index(drop=False, inplace=True)

    ## without following two lines merged dataset would look like:
    #lsr_strt_jmp_len_jmp_strt_lsr_len.columns = ['idx0_weld', 't0_weld', 'diff_idx_prev_jump', 'diff_ms_prev_jump', 'time2power_weld', 'idx0_prev_jump', 't0_prev_jump', 'diff_idx_prev_weld', 'diff_ms_prev_weld', 'time2power_prev_jump']
    lsr_strt_jmp_len = lsr_strt_jmp_len.append(lsr_strt_jmp_len.iloc[-1].copy(), ignore_index=True)
    lsr_strt_jmp_len = lsr_strt_jmp_len.shift(periods=1, axis=0)    
    
    lsr_strt_jmp_len_jmp_strt_lsr_len = pd.merge(lsr_strt_jmp_len, jmp_strt_lsr_len, left_index=True, right_index=True)
    lsr_strt_jmp_len_jmp_strt_lsr_len.columns = ['idx0_weld', 't0_weld', 'diff_idx_prev_jump', 'diff_ms_prev_jump', 'time2power_weld', 'idx0_next_jump', 't0_next_jump', 'diff_idx_weld', 'diff_ms_weld', 'time2power_next_jump']

    lsr_strt_jmp_len_jmp_strt_lsr_len['diff_idx_prev_jump'] = lsr_strt_jmp_len_jmp_strt_lsr_len['diff_idx_prev_jump'].shift(periods=-1, axis=0)
    lsr_strt_jmp_len_jmp_strt_lsr_len['diff_ms_prev_jump'] = lsr_strt_jmp_len_jmp_strt_lsr_len['diff_ms_prev_jump'].shift(periods=-1, axis=0)
    lsr_strt_jmp_len_jmp_strt_lsr_len.columns = ['idx0_weld', 't0_weld', 'diff_idx_next_jump', 'diff_ms_next_jump', 'time2power_weld', 'idx0_next_jump', 't0_next_jump', 'diff_idx_weld', 'diff_ms_weld', 'time2power_next_jump']

    # complete first row entries
    lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 'idx0_weld'] = lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 'idx0_next_jump'] - lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 'diff_idx_weld']
    lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 't0_weld'] = lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 't0_next_jump'] - (lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 'diff_ms_weld']/1000)
    lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 'time2power_weld'] = lsr_strt_jmp_len_jmp_strt_lsr_len.loc[0, 't0_weld'] - df.loc[power, 'time']

    # substract sampling width for accurate result
    lsr_strt_jmp_len_jmp_strt_lsr_len['diff_ms_next_jump'] = lsr_strt_jmp_len_jmp_strt_lsr_len['diff_ms_next_jump'] - sampling_ms
    lsr_strt_jmp_len_jmp_strt_lsr_len['diff_ms_weld'] = lsr_strt_jmp_len_jmp_strt_lsr_len['diff_ms_weld'] - sampling_ms

    return lsr_strt_jmp_len_jmp_strt_lsr_len

