import logging
import pandas as pd
import inspect
import numpy as np

class Weld():
    def __init__(self, x0, y0, x1, y1, expType, prtId, x0_next, y0_next, speed, id, ttlid=None, t0=None, t1=None, t1ttl=None):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.expType = expType
        self.prtId = prtId
        self.x0_next = x0_next
        self.y0_next = y0_next
        self.speed = speed
        self.id = id
        if ttlid == None:
            self.ttlid = self.id
        else:
            self.ttlid = ttlid
        self.t0 = t0
        self.t1 = t1
        self.t1ttl = t1ttl
    
    def dx(self):
        dx = self.x1 - self.x0
        return dx
    def dx_jmp(self):
        dx = self.x1 - self.x0_next
        return dx
    def dy(self):
        dy = self.y1 - self.y0
        return dy
    def dy_jmp(self):
        dy = self.y1 - self.y0_next
        return dy
    def angle(self):
        angle = np.rad2deg(np.arctan2(self.dy(), self.dx()))
        return angle
    def dis(self):
        x2y2 = np.power(self.dx(), 2) + np.power(self.dy(), 2)
        dis = np.power(x2y2, 0.5)
        return dis
    def duration_ms(self):
        duration = self.dis()/self.speed*1000
        return duration
    def changeExp(self):
        pass
    def dis_jmp(self):
        x2y2 = np.power(self.dx_jmp(), 2) + np.power(self.dy_jmp(), 2)
        dis = np.power(x2y2, 0.5)
        return dis

class Part():
    def __init__(self, prtId, param_name):
        self.id = prtId
        self.param_name = param_name

class ParameterSpeed():
    def __init__(self, param_name, infill_down, infill_std, infill_up, contour_down, contour_std, contour_up, contour_simple, edge, partboundary=None, support=None, gap=None, jump=None):
        self.name = param_name
        #1,2,3
        self.infill_down = infill_down
        self.infill_std = infill_std
        self.infill_up = infill_up
        #4,5,6
        self.contour_down = contour_down
        self.contour_std = contour_std
        self.contour_up = contour_up
        #10
        self.contour_simple = contour_simple
        #7
        self.edge = edge

        # not an actual exposure
        self.partboundary = partboundary
        #8
        self.support = support
        self.gap = gap
        self.jump = jump

class Weld_ttl():
    #'idx0_weld', 't0_weld', 'diff_idx_next_jump', 'diff_ms_next_jump', 'time2power_weld', 'idx0_next_jump', 't0_next_jump', 'diff_idx_weld', 'diff_ms_weld', 'time2power_next_jump']
    def __init__(self, idx0_weld, t0_weld, diff_idx_next_jump, diff_ms_next_jump, time2power_weld, idx0_next_jump, t0_next_jump, diff_idx_weld, diff_ms_weld, time2power_next_jump, id):
        self.idx0 = idx0_weld
        self.t0 = t0_weld
        self.idx_len_nxt_jmp = diff_idx_next_jump
        self.duration_ms_nxt_jump = diff_ms_next_jump
        self.t2pow = time2power_weld
        self.idx0_nxt_jmp = idx0_next_jump
        self.t0_nxt_jmp = t0_next_jump
        self.idx_len = diff_idx_weld
        self.duration_ms = diff_ms_weld
        self.t2pow_jump_afterwards = time2power_next_jump
        self.id = id
        self.dur_corr = None

def update_ttlid_nonjumps(welds):
    '''
    Update ttlid in weld class based on zerodistance after weld (contours).
    before: ttlid 1,2,3,4,5,6, ...
    know: ttlid 1,2,3,3,3,4,5,6, ...
    Args: welds
    Returns: welds    
    '''
    ttlid = 0
    for weld in welds:
        weld.ttlid = ttlid
        if weld.dis_jmp() != 0:
            ttlid += 1
    return welds


def corresponding_welds(welds, ttlwelds):
    '''
    create lists for dataframe by iterating welds and
    sum up weld times of welds without measureable jump afterwards based on ttlid

    Args: welds
    Retruns: dataframe
    '''
    duration_eos = []
    duration_ttl = []
    exposuretype = []
    welding_ids = []
    speed = []
    part = []
    distance = []
    duration = 0
    ttlid = 0
    dis = 0
    weld_ids = ''
    for weld in welds:
        # ttlid starts with 0 --> collect all weld ids that equal (they start with 0 too)
        if ttlid == weld.ttlid:
            # weld is measured together with weld before
            duration += weld.duration_ms()
            weld_ids = weld_ids + str(weld.id) + ', '
            expType = weld.expType
            prtId = weld.prtId
            veloc = weld.speed
            dis += weld.dis()
        else:
            # new weld is measured; append previous
            duration_eos.append(duration)
            exposuretype.append(expType)
            speed.append(veloc)
            distance.append(dis)
            part.append(prtId)
            # delete ', ' at the end of string
            weld_ids = weld_ids[:-2]
            welding_ids.append(weld_ids)
            try:
                duration_ttl.append(ttlwelds[ttlid].duration_ms)
            except:
                # no more welds measured (ttl)
                duration_ttl.append(None)

            # reset values
            duration = 0
            duration += weld.duration_ms()
            weld_ids = str(weld.id) + ', '
            expType = weld.expType
            prtId = weld.prtId
            veloc = weld.speed
            dis = weld.dis()
            ttlid = weld.ttlid
    
    # add last eos weld
    duration_eos.append(duration)
    exposuretype.append(expType)
    speed.append(veloc)
    distance.append(dis)
    part.append(prtId)
    # delete ', ' at the end of string
    weld_ids = weld_ids[:-2]
    welding_ids.append(weld_ids)
    try:
        duration_ttl.append(ttlwelds[ttlid].duration_ms)
    except:
        # no more welds measured (ttl)
        duration_ttl.append(None)
            
    df = pd.DataFrame({'dura_eos': duration_eos, 'dura_ttl': duration_ttl, 'expType': exposuretype, 'dis': distance, 'prtId': part, 'speed': speed, 'weld_ids': welding_ids})

    return df


def corresponding_error(df):
    '''
    Calculate error between eos and ttl
    relative and absolute error

    Args: df
    Retruns: df
    '''
    df['error_abs_ms'] = df['dura_ttl'] - df['dura_eos']
    df['error_rel'] = (df['dura_eos'] - df['dura_ttl']) / df['dura_eos']

    df['eosdiff_prv'] = df['dura_eos'].diff(periods=1)
    df['eosdiff_nxt'] = df['dura_eos'].diff(periods=-1)
    df['ttldiff_prv'] = df['dura_ttl'].diff(periods=1)
    df['ttldiff_nxt'] = df['dura_ttl'].diff(periods=-1)

    df['eosttl_prv'] = (df['eosdiff_prv']-df['ttldiff_prv'])/df['eosdiff_prv']
    df['eosttl_nxt'] = (df['eosdiff_nxt']-df['ttldiff_nxt'])/df['eosdiff_nxt']

    return df

def io_position(df, error_position=-1, min_weld_len=5, error_treshold=0.05, ntimes=2):
    '''
    finds index of welds with temporal length missmatch (relative error) of error_treshold,
    temporal target length (eos) > min_weld_len until index of error_position or end of dataframe (-1),
    which are more than ntimes of error_treshold longer or shorter compared to welds before and after.
    Returns only last correct single peak (not "absolut last" io position)

    Args: df, error_position=-1, min_weld_len=5, error_treshold=0.05, ntimes=2
    Retruns: iopos
    '''
    df_noviol = df[:error_position].loc[(df.dura_eos >= min_weld_len) & (abs(df.error_rel) <= error_treshold) & (abs(df.eosdiff_prv) > ntimes*error_treshold*min_weld_len) & (abs(df.eosdiff_nxt) > ntimes*error_treshold*min_weld_len)].copy()
    if len(df_noviol) == 0:
        iopos = -1
    else:
        iopos = df_noviol.index[-1]
    return iopos


def error_position(df, min_weld_len=1, error_treshold=0.2):
    '''
    returns position (idx) of first wrong vector (pos_err) in eos (error_rel > error_treshold) that is not too short (> min_weld_len)
    pos_err is not the exact index of the error, but an index where allocation eos-ttl is definitively wrong
    called functon error_determination() tries to find out error type, shift and correct allocation for pos_err

    Args: df, min_weld_len=1, error_treshold=0.2
    Returns: pos_err, pos_io, true_pos_err
    '''

    logger = logging.getLogger(inspect.currentframe().f_code.co_name)

    # find error position
    df_viol = df.loc[(df.dura_eos >= min_weld_len) & (abs(df.error_rel) >= error_treshold)].copy()
    if len(df_viol) == 0:
        # no error left
        pos_err = -1
        logger.info(f'Success! No more errors left with min_weld_len: {min_weld_len}, error_treshold: {error_treshold}')
    else:
        pos_err = df_viol.index[0]

    # find last accepted position
    pos_io = io_position(df.loc[:pos_err], pos_err)

    return pos_err, pos_io


def find_unique_welds_eos(df, pos_err, min_weld_len=5, error_treshold=0.05, ntimes=2, col='dura_eos'):
    '''
    find welds in eos that are kind of unique / outstanding in time row
    that differ (temporal length) to prv and next welds afterwards <pos_err> by
    ntimes * error_threshold
        len     typical error
        10      < 0.01
        5       < 0.02
        2       < 0.05
        1       < 0.1
    Args: df, pos_err, min_weld_len=5, error_treshold=0.05, ntimes=2
    Returns: unique_welds
    '''
    #unique_welds = df[pos_err:].loc[(df[pos_err:].dura_eos >= min_weld_len) & (abs(df[pos_err:].eosdiff_prv) > ntimes*error_treshold*min_weld_len) & (abs(df[pos_err:].eosdiff_nxt) > ntimes*error_treshold*min_weld_len)].copy()
    unique_welds = df.loc[(df[col] >= min_weld_len) & (abs(df.eosdiff_prv) > ntimes*error_treshold*min_weld_len) & (abs(df.eosdiff_nxt) > ntimes*error_treshold*min_weld_len)].copy()
    # loc index with other filters in one row returns empty dataframes --> splitted into two lines
    unique_welds = unique_welds.loc[pos_err:]
    return unique_welds


def matching_unique(df, pos_err, min_weld_len=5, error_treshold=0.05, ntimes=2, win=10, max_iter=1):
    '''
    find outstanding weld in eos
        length is within +/- win unique
        prev and next differ ntimes*error_treshold
        nominal length is above 5 ms
        length is present in +/- win only once
        not first or last position in window
    find same unique weld in ttl measurement

    Version: 07.12.2022

    Returns: shift, unique_welds_eos.iloc[0].index
    '''
    not_found = True
    i = 0
    while(not_found):
        df_win = df.loc[pos_err-win:pos_err+win].copy()
        # filter unique in window
        unique_welds_eos = df_win.loc[(df_win['dura_eos'] >= min_weld_len) & (abs(df_win.eosdiff_prv) > ntimes*error_treshold*min_weld_len) & (abs(df_win.eosdiff_nxt) > ntimes*error_treshold*min_weld_len)].copy()
        unique_welds_ttl = df_win.loc[(df_win['dura_ttl'] >= min_weld_len) & (abs(df_win.ttldiff_prv) > ntimes*error_treshold*min_weld_len) & (abs(df_win.ttldiff_nxt) > ntimes*error_treshold*min_weld_len)].copy()
        #if len(unique_welds_eos) != 0 & len(unique_welds_ttl) != 0 and len(unique_welds_eos) == len(unique_welds_ttl):
        
        
        # if unique(s) is/are found and not first or last x places in window
        x = 2
        if (len(unique_welds_eos) != 0) & (len(unique_welds_ttl) != 0):
            
            for idx in unique_welds_eos.index:
                # eos value should not be the first or last two entries in window
                # and length is unique in window
                l = unique_welds_eos.loc[idx, 'dura_eos']
                n = len(unique_welds_eos.loc[(unique_welds_eos['dura_eos'] > l-ntimes*error_treshold) & (unique_welds_eos['dura_eos'] < l+ntimes*error_treshold)])
                if (idx > pos_err-win+x) and (idx < pos_err+win-x) and n == 1:
                    # not last or first in eos and nominal length is unique (n==1)
                    # find possible matches by length and tol
                    candidates_ttl = unique_welds_ttl.loc[(unique_welds_ttl['dura_ttl'] >= (l - l*error_treshold)) & (unique_welds_ttl['dura_ttl'] <= (l + l*error_treshold))]
                    if len(candidates_ttl) == 1:
                        # one match found
                        not_found = False
                        shift = candidates_ttl.index[0] - idx
                        return shift, unique_welds_eos.index[0]

                    break

            # use match
            
        
        pos_err += 6
        if max_iter == i:
            return 100, -1
        i += 1


def swelds(df, crit_len=0.042):
    '''
    find really short welds "swelds" based on eos target legnth,
    that are maybe not measured.
    crit_len should be 2x sampling distance 
    Args: df, crit_len=0.042)
    Returns: swelds
    '''
    swelds = df.loc[df['dura_eos'] < crit_len]
    return swelds


def rel_error(eos, ttl):
    '''
    compute relative error of two arrays / numbers
    '''
    rel_err = (eos-ttl)/eos
    return abs(rel_err)


def matching_sequence(df, seq_strt_eos, seq_len=5, max_iter=4, mode=-1):
    '''
    This function should find the shift of a sequence using iterativ trial of shifts in one direction.
    may repeat in the other direction (mode). standard is backwards (missing measured weld).
    will may not find a result if an error is within the sequence (e.g. too short non measurable weld)
    welds with nominal length < 1 ms will be ignored (variance too high)
    diffs prv and nxt < 0.05 will be ignored (variance too high)
    compare a sequence of df by comparation of duration, diff previous and diff next.
    try several shifts iteratively, e.g. up to three to find true shift
    Return -1: means sequence in ttl is shifted by one backwards (one missing weld in ttl against eos before sequence)
    Return 100: means no shift value was found within iteration count

    Changelog: 07.02.2023
    error_treshold=0.1 -> 0.075 and abort criteria len(unique_welds) == 0 -> e is null -> cannot find
    
    TODO find additionally by maxima if values differ at least by x % ? does only work if maximum is in sequence (umkehrpunkt)

    Args: df, seq_strt_eos, seq_len=5, max_iter=4, mode=-1
    Returns: shift
    
    TODO error codes einführen für die verschiedenen abbrüche
    '''

    logger = logging.getLogger(inspect.currentframe().f_code.co_name)

    not_found = True
    # if mode == -1:
    #     shft = -1
    # else:
    #     shft = 1
    shft = 0
    
    #unique_welds = find_unique_welds_eos(df[seq_strt_eos:seq_strt_eos+seq_len], seq_strt_eos, min_weld_len=1, error_treshold=0.1, ntimes=2)
    unique_welds = find_unique_welds_eos(df.loc[seq_strt_eos:seq_strt_eos+seq_len], seq_strt_eos, 1, 0.075, 2)
    
    # criteria e: len > 0 for acceptance. cannot be fulfilled
    if len(unique_welds) == 0:
        logger.info('Warning: len(unique_welds) equals zero. Function cannot find a matching_sequence!')
        return 100
    # accepted difference between eos and ttl regarding relative error of duration
    tol_len = 0.1
    # accepted relative difference between eos and ttl regarding relative error of differences (prv, nxt). typically around 0.2 to 0.5, but sometimes above 10 %
    # changed from 0.1 to 0.15 (01.02.2023)
    tol_diff = 0.2
    # dura_eos in ms
    at_least_one_longer = 1
    # minimum difference between following welds for filter. should be at least twice of sampling_ms
    # if too high, not enough positions found; if too low, then measurement tolerance influences too much
    tol_sampling = 0.10
    # minimum duration in msec
    tol_dura = 1

    # reset save_rel_err_prv_nxt
    save_rel_err_prv_nxt = []

    # check for swelds in sequence
    if len(swelds(df[seq_strt_eos:seq_strt_eos+seq_len])) != 0:
        # not implemented yet. try another sequence. maybe repeat at sweld position
        logger.info('swelds found in sequence - abort')
        return 101
    else:
        # function requieres no swelds present in sequence. otherwise shift within sequence -> cannot compute
        
        # create numpy arrays for duration, temporal diff to previous and next
        seq_dura_eos = df.loc[seq_strt_eos:seq_strt_eos+seq_len, 'dura_eos'].values
        seq_eosdiff_prv = df.loc[seq_strt_eos:seq_strt_eos+seq_len, 'eosdiff_prv'].values
        seq_eosdiff_nxt = df.loc[seq_strt_eos:seq_strt_eos+seq_len, 'eosdiff_nxt'].values
        
        logger.info(f'seq_dura_eos: {["%.2f" % elem for elem in seq_dura_eos ]}')
        #logger.info(f'seq_eosdiff_prv: {seq_eosdiff_prv}')
        #logger.info(f'seq_eosdiff_nxt: {seq_eosdiff_nxt}')

        # create filter for values greater <tol_dura> and sampling differences greater <tol_sampling>
        filter_len = np.where(seq_dura_eos > tol_dura)
        filter_prv = np.where(abs(seq_eosdiff_prv) > tol_sampling)
        filter_nxt = np.where(abs(seq_eosdiff_nxt) > tol_sampling)

        if len(seq_dura_eos) != (seq_len + 1):
            logger.info(f'true sequence length ({len(seq_dura_eos)}) does not equal nominal seq_len. Abort with errorcode')
            return 100
        else:
            if len(filter_len) == 0 or len(filter_prv) == 0 or len(filter_nxt) == 0:
                logger.info('no values within filter range. no robust measurement possible. try another or longer sequence')
                return 100

        while(not_found):
            # find coresponding ttl values (by index)

            seq_dura_ttl = df.loc[seq_strt_eos+shft:seq_strt_eos+seq_len+shft, 'dura_ttl'].values
            seq_ttldiff_prv = df.loc[seq_strt_eos+shft:seq_strt_eos+seq_len+shft, 'ttldiff_prv'].values
            seq_ttldiff_nxt = df.loc[seq_strt_eos+shft:seq_strt_eos+seq_len+shft, 'ttldiff_nxt'].values

            logger.info('######################### sequence search #########################')
            logger.info(f'seq_dura_ttl: {seq_dura_ttl}')
            #logger.info(f'seq_ttldiff_prv: {seq_ttldiff_prv}')
            #logger.info(f'seq_ttldiff_nxt: {seq_ttldiff_nxt}')

            # error in length is small
            # error in diff_prv is small
            # error in diff_nxt is small
            # at least one of sequence is greater 1 ms
            # at least one of sequence is unique

            # abort if length missmatch. happens with pos_io nearby pos_err and shift trial "touches" pos_io
            if len(seq_dura_eos) != len(seq_dura_ttl):
                logger.info(f'Lenght missmatch seq_eos and seq_ttl!')
                return 100
            # calculate error for corresponding values
            a = rel_error(seq_dura_eos, seq_dura_ttl)
            b = rel_error(seq_eosdiff_prv, seq_ttldiff_prv)
            c = rel_error(seq_eosdiff_nxt, seq_ttldiff_nxt)

            # apply filter to only use values greater <tol_dura> and sampling differences greater <tol_sampling>
            # use only maximum because of e.g. three with same length follow eachother and they are shifted by one, then two seem to be correct
            a_m = (max(a[filter_len]))
            b_m = (max(b[filter_prv]))
            c_m = (max(c[filter_nxt]))
            d_m = (max(seq_dura_eos))
            e = (len(unique_welds))

            logger.info(f'a,b,c: {a,b,c}')
            logger.info(f'a_m,b_m,c_m,d_m,e filtered: {a_m,b_m,c_m,d_m,e}')
            logger.info(f'seq_eosdiff_prv: {seq_eosdiff_prv}')
            logger.info(f'seq_ttldiff_prv: {seq_ttldiff_prv}')
            logger.info(f'seq_eosdiff_nxt: {seq_eosdiff_nxt}')
            logger.info(f'seq_ttldiff_nxt: {seq_ttldiff_nxt}')

            # logger.info(f'a[filter_len]: {a[filter_len]}')
            # logger.info(f'b[filter_prv]: {b[filter_prv]}')
            # logger.info(f'c[filter_nxt]: {c[filter_nxt]}')

            

            if a_m < tol_len and b_m < tol_diff and c_m < tol_diff and d_m > at_least_one_longer and e > 0:
                # match found - return function
                not_found = False
                return shft
            
            else:
                if a_m < tol_len and d_m > at_least_one_longer and e > 0:
                    # if only prev and next rel errors do not fit, then save value and use minimum?
                    save_rel_err_prv_nxt.append(abs(b_m) + abs(c_m))
                # match not found - iterate shift
                if mode == -1:
                    shft -= 1
                else:
                    shft += 1

            # max_iter reached - break while
            if abs(shft) > max_iter:
                logger.info('max iteration count reached - abort')
                break
    return 100


def del_shortest(df, pos_io, pos_err):
    # deletes shortest in area

    logger = logging.getLogger(inspect.currentframe().f_code.co_name)

    smallest = df[pos_io:pos_err+1].dura_eos.nsmallest(5).index[0]
    logger.info(f'DELSHORTEST: {smallest} will be deleted.')
    df.loc[smallest:, df.columns != 'dura_ttl'] = df.loc[smallest:, df.columns != 'dura_ttl'].shift(periods=-1, axis=0)
    #df.loc[smallest-2:smallest+2]
    # drop rows where all values are missing
    df.dropna(how='all', inplace=True)
    return df


def chk_err_move(pos_err, df_new):
    '''
    calculates error values for dataframe and returns movement of error.
    positive value -> error moves forward -> good solution

    Args: pos_err, df_new
    Returns: (pos_err_new - pos_err)
    '''

    logger = logging.getLogger(inspect.currentframe().f_code.co_name)

    #df = corresponding_error(df)
    df_new = corresponding_error(df_new)
    pos_err_new, pos_io_new = error_position(df_new)
    
    
    logger.info(f'pos_err changes {pos_err} to {pos_err_new}; pos_io_new: {pos_io_new}')
    ## err_move
    # -1: one backwards --> maybe one of several missing welds
    # < -1: several backwards --> wring try, not a correct solution
    # 0: no change --> maybe one of several missing welds
    # > 0: loss moves forwards --> correct solution
    err_move = (pos_err_new - pos_err)
    logger.info(f'pos_err_new - pos_err {err_move}')

    
    return err_move, df_new

    #(done only if shift is negative or pos is earlier and short welds are available)

    # not measured weld: del one short is correct --> pos_err -= 1 and negative shift += 1 (abs(shift)-=1)
    # jump not measured (ttl shows one eos two welds): -> negative shift like short weld -> set ttlid of both vectors equal -= 1 all following
    # non existant jump measured (eos weld is splitted) -> shift is positive --> try combination of wrong pos with next and prev via diff_nxt and diff_prv -> pos_io moves afterwards or pos_err moves more then 2 --> success
        # no success: either reduce min_weld_len and max_err or find next sequence shift - shift from there and ignore data in between
    
    # del one short not correct --> pos_err -= 1 and 


def compare_temporal_weld_len(ttlid, welds, ttlwelds):
    # input ttl weld id returns length of sum of corresponding eos welds and ttl weld length
    criteria = lambda w: w.ttlid == ttlid
    welds_len = np.sum([weld.duration_ms() for weld in list(filter(criteria, welds))])
    ttlwelds_len = ttlwelds[ttlid].duration_ms
    return welds_len, ttlwelds_len

def main_redefinelaserpathstarts(welds, ttlwelds):
    '''
    Motivation: count of eoswelds and ttlwelds differ because of measurement error

    Am 26.01. verändert und solver und error_determination vereinigt

    Create dataframe from classes and compute temporal weldlength error
    While as long as count of eoswelds and ttlwelds differ
        Calculate first/next error position and try to solve it incl. checks for success
        recalculate dataframe
    calculate final error position and if completed calculate eos welds_updated
    return corrected eoswelds if full dataframe could succeeded

    Args: eoswelds and ttlwelds as classes
    Returns: corrected eoswelds
    '''
    ##############################################################################
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    #out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    #logger.info(out)
    ##############################################################################

    # calculate df from weld classes
    df = corresponding_welds(welds, ttlwelds)
    # (re-)calculate error in dataframe
    df = corresponding_error(df)

    ## approx. count of missing welds and missing jumps
    err_forecast = test_len_diff(df)

    while(test_len_diff(df)>0):
        trial_cnt = test_len_diff(df)
        if (err_forecast - trial_cnt)%100 == 0:
            print(f'{(err_forecast - trial_cnt)} of approx. {err_forecast} solved.')
        # found out last io and first error position
        pos_err, pos_io = error_position(df)
        logger.info(f'test_len_diff(df) = {test_len_diff(df)}')
        logger.info(f'pos_err, pos_io = {pos_err, pos_io}')

        # if pos_io >= 53619:
        #     break

        # try solution and check movement (chk >= 0: error moves forward)
        #df_new, done_op = solver(df, pos_err, pos_io)
        df_new = solver_error_determination(df, pos_err, pos_io)

        # stop at index for debugging
        debugging = False
        debugging_pos_err = 23815
        if pos_err == debugging_pos_err and debugging == True:
            return None, df


        #chk = chk_err_move(pos_err, df_new)
        logger.info(f'len(df_new): {len(df_new)}')
        df = corresponding_error(df_new)
        
        
        # logger.info(f'done_op = {done_op}')
        # logger.info(f'check = {chk}')
        # if chk >= -1:
        #     # if one eos entity is dropped then its position moves one forward if there is a second issue previously
        #     # if all previous issues are solved, then loss moves forwards and chk > 0
        #     df = corresponding_error(df_new)
        # else:
        #     # try else
        #     logger.info('else entered')
        #     break

    pos_err, pos_io = error_position(df)
    print(pos_err, pos_io)
    if pos_err == debugging_pos_err and debugging == True:
            return None, df
    
    # length difference is zero means same len of ttl and eos. pos_err and pos_io are at the end of dataframe
    if test_len_diff(df) == 0 and pos_err == -1 and pos_io == -1:
        print('Success!')

        welds_updated = update_ttlid_solved(df, welds, ttlwelds)

        return welds_updated, df, welds

 