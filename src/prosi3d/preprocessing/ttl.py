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