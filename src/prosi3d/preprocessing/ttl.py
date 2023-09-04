import logging
import inspect

def tJumpTTL(layer, path, sampling_ms=0.02):
    '''
    03.11.2022  modified to input path as argument

    Gives dataframes with temporal lengths and positions of found jumps and laservectors in ttl signal of entered layer.

    Procedure:
    laser is on when ttl values above thresholds
    filter those and copy indexes to column
    calculate difference of idx column
    where idx-difference is > 1 a jump was in between and vice versa -> row gives start of weld and diff_idx length of jump to this row/time
    filtered and multiplied with sampling time gives temporal length of jump
    
    Args: layer,sampling_ms=0.02
    Returns: jmp_strt_lsr_len, lsr_strt_jmp_len
    '''
    #print('>>>>>>>>>> ', inspect.currentframe().f_code.co_name, inspect.getargvalues(inspect.currentframe()).locals)
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    logger.info(out)

    #ttldir= R"C:\Users\ringel\Lokal\Python-local\ProSi3D\brosev2_19112021\4ch_raw"
    eostxtfile, paramfile, jobfile, vecdir, ttldir, resdir, logdir, _ = folder2Files(path, 0)
    
    f = ttldir + "\\ch4raw_" + str(layer).zfill(5) + ".h5"
    df = pd.read_hdf(f, 'df')
    df.columns = ['time', 'lse', 'ttl', 'kse_bp', 'kse_rec']
    df = df.drop(['lse', 'kse_bp', 'kse_rec'], axis=1)
    
    # two treshold values for beginning x samples of layer and rest --> indexboarder
    tresh1 = 1
    tresh2 = -1


    # ## change for Fabian
    # tresh1 = 3
    # tresh2 = 3
    # ## end of change


    # difference of indexes marks laserweld by values greater than one and by that the next jump
    min_len_idx = 1

    # first value above threshold is laser on for the first time
    power = df['ttl'].loc[(df['ttl'] >= tresh1)].index[0]
    # loc gets index, iloc counts places

    # differences between each line
    df['diffs'] = df['time'].diff()
    # use median of timediffs for sampling time step in ms --> why is that 0.04 ms? it should be 0.02
    sampling_ms = df['diffs'].median()*1000
    logger.info('median sampling time steps median [ms]: ' + str(sampling_ms))
    
    # threshold boarder, empiric value for 50kHz was around row 7000 -> 0.3 s for any sampling frequ
    indexboarder = power + int(0.294/sampling_ms*1000)
    
    # df_jumps = all values lower then thresholds represent jumps and vice versa for welds
    df_jumps = df.loc[((df['ttl'] < tresh1) & (df.index < indexboarder)) | ((df['ttl'] < tresh2) & (df.index >= indexboarder))].copy()
    df_laser = df.loc[((df['ttl'] >= tresh1) & (df.index < indexboarder)) | ((df['ttl'] >= tresh2) & (df.index >= indexboarder))].copy()

    # diff gives rowdifferences of all. filtered and cumulative sum gives timerow for filter
    df_jumps['cum-sum'] = df_jumps.diffs.cumsum()

    # new column with index integers
    df_jumps['idx'] = df_jumps.index
    # values greater 1 in diff_idx are idx-lengths of laserwelds between jumps
    '''
    idx diff_idx
    11  NaN
    12  1
    47  35
    48  1
    49  1
    '''
    df_jumps['diff_idx'] = df_jumps.idx.diff()

    # rows with start of jump end length of weld before
    jmp_strt_lsr_len = df_jumps.loc[df_jumps['diff_idx'] > min_len_idx].copy()
    
    ## same other way round would find length of jumps
    # cumsum of diffs gives timerow
    df_laser['cum-sum'] = df_laser.diffs.cumsum()
    # new column with index integers
    df_laser['idx'] = df_laser.index
    # new column with differences between indices
    df_laser['diff_idx'] = df_laser.idx.diff()
    
    # if difference between indices greater 1 then laser was off for that time
    lsr_strt_jmp_len = df_laser.loc[df_laser['diff_idx'] > min_len_idx].copy()
    
    # lsr_strt_jmp_len['diff_ms'] = lsr_strt_jmp_len['diff_idx'].multiply(sampling_ms) 
    # jmp_strt_lsr_len['diff_ms'] = jmp_strt_lsr_len['diff_idx'].multiply(sampling_ms)

    lsr_strt_jmp_len['prev_idx'] = lsr_strt_jmp_len.index - lsr_strt_jmp_len['diff_idx']
    lsr_strt_jmp_len['diff_ms'] = (lsr_strt_jmp_len['time'] - df.loc[lsr_strt_jmp_len['prev_idx'], 'time'].values)*1000

    jmp_strt_lsr_len['prev_idx'] = jmp_strt_lsr_len.index - jmp_strt_lsr_len['diff_idx']
    jmp_strt_lsr_len['diff_ms'] = (jmp_strt_lsr_len['time'] - df.loc[jmp_strt_lsr_len['prev_idx'], 'time'].values)*1000

    # timelaser in df_laser_start gives timeval for laservector start (high ramp) --> use for synchronization with eos data
    lsr_strt_jmp_len['timelaser'] = lsr_strt_jmp_len['time'] - df.loc[power, 'time']
    jmp_strt_lsr_len['timelaser'] = jmp_strt_lsr_len['time'] - df.loc[power, 'time']

    laser_on = df_laser.shape[0]
    laser_off = df_jumps.shape[0]
    laser_off_rec = df_jumps.loc[df_jumps.index <= power].shape[0]

    # output found jump and weld count
    weld_cnt = lsr_strt_jmp_len.shape[0]
    jump_cnt = jmp_strt_lsr_len.shape[0]
    
    # dont use same quotation marks (",') inside and outside fstrings arguments
    logger.info(f"Measured jump samples: {laser_off} (rec: {laser_off_rec}) with total time {df_jumps['cum-sum'].iloc[-1]} (rec: {df['time'].loc[power] - df['time'].iloc[0]}); count: {jump_cnt}")
    logger.info(f"Measured laser samples: {laser_on} with total time {df_laser['cum-sum'].iloc[-1]}; count: {weld_cnt}")
    logger.info(f"Total layer time: {df['time'].iloc[-1] - df['time'].iloc[0]} started at {df['time'].iloc[-1]}")
    
    ## some error may results from not exact sampling. many samples have 0.021 instead of 0.02 ms timestamps
    
    return jmp_strt_lsr_len, lsr_strt_jmp_len

def test_len_diff(df):
    eos = len(df.loc[~df['dura_eos'].isna()])
    ttl = len(df.loc[~df['dura_ttl'].isna()])
    return eos - ttl


def update_ttlid_solved(df, welds, ttlwelds):
    '''
    Overwrite ttlid with index of df.
    Update weld.id 
    
    Return: welds
    '''
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    # initialize counter
    ttlidx = 0
    cnt_del = 0

    # df is based on ttl signal. rows represent weld measurements. column weld_id collects eos welds measured as one weld (e.g. conturs).
    weld_id_lst = [np.array(x.split(',')).astype(int) for x in df.weld_ids]
    #weld_id_lst_flat = np.concatenate(weld_id_lst)#.ravel()
    
    # iterate weld_id_lst from dateframe where one row equals one measureable weld
    for weld_ids in weld_id_lst:
        init_one_measurement = 0

        # weld_id is a valid id only. weld_id != missing ids
        for weld_id in weld_ids:
            
            welds[weld_id].ttlid = ttlidx
            logger.info(f'weld_id: {weld_id}; .ttlid set to: {ttlidx}; ttlwelds[ttlidx].t0 = {ttlwelds[ttlidx].t0}')

            # apply t0 for single and multi measured
            if init_one_measurement == 0:
                welds[weld_id].t0 = ttlwelds[ttlidx].t0
                welds[weld_id].t1ttl = welds[weld_id].t0 + ttlwelds[ttlidx].duration_ms/1000
            else:
                # 01.03.2023 division with 1000 added
                #welds[weld_id].t0 = ttlwelds[ttlidx].t0 + welds[weld_id-init_one_measurement].duration_ms()/1000
                welds[weld_id].t0 = welds[weld_id_prv].t0 + welds[weld_id_prv].duration_ms()/1000
                #welds[weld_id].t1ttl = welds[weld_id].t0 + ttlwelds[ttlidx].duration_ms/1000

            ## mark missing welds with ttlid = -1
            # if weld id equals next integer value none is missing
            if cnt_del == weld_id:
                cnt_del += 1
            else:
                # if not one is missing. update ttlid with -1
                welds[cnt_del].ttlid = -1
                cnt_del += 2

                ## check would be:
                #np.isin(cnt_del, np.concatenate(weld_id_lst)) == False --> not part of measurement
            
            weld_id_prv = weld_id
            init_one_measurement += 1

        ttlidx += 1
    return welds
