import logging
import inspect

def error_determination(df, pos_err, pos_io, error_treshold=0.2):
    '''

    REPLACED BY solver_error_determination() 07.02.2023

    tries to find out what kind of error accured - which shift direction
    logic:
    - use df between pos_io and pos_err+20
    - try to find out the shift around err_pos by matching_sequence
    - 




    errortype ==
        0: shift is null, does not work
        1: missing weld assumed between pos_io and true_pos_err
        2: missing weld assumed between pos_io and pos_err
        3: missing jump assumed between pos_io and true_pos_err
        4: missing jump assumed between pos_io and pos_err
        5: broken weld assumed between pos_io and pos_err
        -1: could not determine

    Args: df, pos_err, error_treshold
    Returns: error_type, shift, pos_err
    
    '''
    ##############################################################################
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    #out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    #logger.info(out)
    logger.info(f'len(df), pos_err, pos_io, error_treshold: {len(df), pos_err, pos_io, error_treshold}')
    ##############################################################################
    
    df_bkp = df.copy()
    df = df.loc[pos_io:pos_err+20].copy()
    # temporal length of eos at error position
    dura_eos_err = df.loc[pos_err, 'dura_eos']

    ## try to find out shift using matching_sequence and matching_unique

    # calculate shift at error position - robustness not tested yet (30.11.2022)
    shift = matching_sequence(df, pos_err)
    if shift == 100:
        # try opposite direction
        shift = matching_sequence(df, pos_err, seq_len=5, max_iter=4, mode=1)


    # test shift in both directions severall times 
    tests = 0
    while(shift == 100 and tests <= 6):
        mode = -1
        if mode==-1:    
            try:
                # searchpoint afterwards err_pos; negative direction
                shift = matching_sequence(df, pos_err+(tests*2), seq_len=5, max_iter=4, mode=-1)
            except:
                print('matching_sequence() fails')
        if mode==1:
            try:
                # searchpoint afterwards err_pos; positive direction
                shift = matching_sequence(df, pos_err+(tests*2), seq_len=5, max_iter=4, mode=1)
            except:
                print('matching_sequence() fails')

        tests += 1
        mode = mode*-1

    # calculate shift by single unique
    # not robust yet, maybe because of small window
    #print(f'shift before shift_unique(): {shift}')
    if shift == 100:
        try:
            shift_unique, idx_unique = matching_unique(df_bkp, pos_err, min_weld_len=5, error_treshold=0.05, ntimes=2, win=10)
            logger.info(f'shift_unique = {shift_unique}')
            if shift_unique != 100:
                shift = shift_unique
                logger.info(f'use shift by unique instead of shift by sequence: {shift_unique}')
        except:
            shift_unique = 100
            idx_unique = -1
    
    if shift == 100 and shift_unique == 100:
        try:
            shift_unique, idx_unique = matching_unique(df_bkp, pos_err, min_weld_len=3, error_treshold=0.05, ntimes=2, win=10)
            print(shift_unique)
            if shift_unique != 100:
                shift = shift_unique
                logger.info(f'use shift by unique instead of shift by sequence: {shift_unique}')
        except:
            shift_unique = 100
            idx_unique = -1

    

    # compare shift values
    # if (shift != 100) and (shift != shift_unique):
    #     print(f'WARNING: shift by sequence: {shift} does not match shift by unique: {shift_unique} at index: {idx_unique}')

    # TODO if no shift was found may try another shift finding method

    # check if potentially non measurable short welds occur before pos_err
    # only meaningfull if dataframe starting with last pos_io was entered in error_determination()
    # if true, then non measured welds are not present --> failure should be non measured jump
    sweld = swelds(df.loc[:pos_err])
    first_eos_sweld = sweld.index[0]

    # # calculate candidates for dura_eos_err in ttl values in between pos_io and pos_err by temporal length
    # candidates_sweld2err = df.loc[(df['dura_ttl'] < (error_treshold+1)*dura_eos_err) & (df['dura_ttl'] > (1-error_treshold)*dura_eos_err)].copy()
    # candidates_sweld2err = candidates_sweld2err.loc[first_eos_sweld:pos_err]

    ## calculate ttl-candidates for eos duration at error position (dura_eos_err) in ttl values by temporal length and error_treshold
    candidates = df.loc[(df['dura_ttl'] < (error_treshold+1)*dura_eos_err) & (df['dura_ttl'] > (1-error_treshold)*dura_eos_err)].copy()
    # in between pos_io and pos_err 
    candidates_io2err = candidates.loc[:pos_err]
    # in between first sweld and pos_err 
    candidates_sweld2err = candidates.loc[first_eos_sweld:pos_err]
    # from pos_err
    candidates_err2end = candidates.loc[pos_err:]

    if shift == 0:
        return 0, shift, pos_err

    ## 1 shift negativ: missing weld or missing jump in measurement
    
    if shift < 0:
        # 1A:
        # unique match in temporal length between pos_io and pos_error indicates true position (ttl weld count < eos count)
        if len(candidates_io2err) == 1:
            # true position of error position
            true_pos_err = candidates_io2err.index[0]
            shift_true_pos = true_pos_err - pos_err
            if shift_true_pos != shift:
                print('WARNING: shift_true_pos != shift')
                shift = shift_true_pos
                # may abort here

            # position found, failure must be previous
            sweld = swelds(df.loc[:true_pos_err+1])
            # could be missing measurement of weld or missing measurement of jump
            # if shift < -1 then failure types could be combined ?!
            if len(sweld) == 0:
                # no swelds found - should be missing jump
                # Fehlenden sprung validieren? Größter absoluter fehler sollte prv oder next enstprechen bei gleichzeitig hohem rel fehler
                # nur sinnvoll mit welds > 0.042 (2*sampling_width)
                
                df_missing_jumps = df.loc[((df['error_abs_ms'] < df['eosdiff_nxt']+(error_treshold*df['eosdiff_nxt'])) & (df['error_abs_ms'] > df['eosdiff_nxt']-(error_treshold*df['eosdiff_nxt'])) & df['dura_eos'] > 1)]
                df_missing_jumps = df_missing_jumps.loc[pos_io:pos_err+1]
                
                ## 3: true error position found and no swelds present --> missing jump assumed
                return 3, shift, true_pos_err

            else:
                # should be sweld
                # how many? -> shift
                # test error of sweld --> if false: test missing jump --> if false: shift sequence and ignore values
                print(f'ERROR_DETERMINATION: shift = {shift}. Sweld count = {len(sweld)}. Drop shortest!')
                
                ## 1: true error position found and swelds are present --> missing weld assumed
                return 1, shift, true_pos_err
                
        # 1B:
        # no unique match
        else:
            if len(sweld) == 0:
                # no swelds found - should be missing jump
                print('ERROR_DETERMINATION WARNING: No potentially non measurable short welds found (pos_io:pos_err)!')
                ## TODO either try already here or return guessed. try -> return if false -> save returnment of error_determination()
                
                ## 4: true error position not found and no swelds are present --> missing jump assumed
                return 4, shift, pos_err
            else:
                # should be sweld
                # how many? -> shift
                # test error of sweld --> plausibility
                # action for 
                print(f'ERROR_DETERMINATION: shift = {shift}. Sweld count = {len(sweld)}. Drop shortest!')
                # TODO test sweld dropping
                ## 2: true error position not found and swelds are present --> missing jump assumed
                return 2, shift, pos_err

    ## 2 shift positive: must be broken weld (jump measured inside eos vector where no nominal jump is defined)
    
    # if shift is not found --> =100 --> function enters shift positive
    else:
        if shift == 100:
            return -1, shift, pos_err
        else:
            
            # TODO analog missing jump

            ## 5: broken weld
            return 5, shift, pos_err

    # if nothing clear, exit function find next valid shift. shift it. mark area as not trustfull or delete/drop it directly


def solver_error_determination(df, pos_err, pos_io, error_treshold=0.2):
    '''
    true error is in between pos_io and pos_err in df

    pos_err could be the true_error_position
        missing weld not possible because pos_err is calculated for welds > 1 ms --> found position should be measured
        missing jump afterwards pos_err possible
        additional jump / split weld possible
    
    pos_err could be afterwards true_error_position
        missing weld possible --> shift < 0
        missing jump possible --> shift < 0
        additional jump possible --> shift > 0
    
    multiple error types could counterbalance shift
    most errors are missing welds



    1 ) function tries to find out the shift in the area of err_pos
        using matching sequence and matching unique
        using unique candidates in dura_ttl for the dura_eos value at error position
            shift is typically 1 or 2 and < 5
    2 ) shift == 0: shift calculation went wrong, counterbalancing errors or sth else, cannot resolve
    3 ) shift == 100: max_iteration_stop; no shift found

    4 ) shift == 101: sweld within sequence (which is used for shift calculation). not computable --> TODO try another position afterwards

    5 ) shift < 0: missing weld or missing jump. (always test missing jump first)
            search for swelds in eos
            
                if sweld exist (always check for missing weld again, after one sweld is dropped)
                    if exactly one --> try
                    else --> try shortest until either 5 times tried or if shift is valid until shift is reached
                    if error moves only one index --> another not detected sweld or missing jump
                else then missing jump --> typically at pos_err because two following welds are "added"
                    TODO check and solve

    6) shift > 0: additional jump
        TODO
                    







    errortype ==
        0: shift is null, does not work
        1: missing weld assumed between pos_io and true_pos_err
        2: missing weld assumed between pos_io and pos_err
        3: missing jump assumed between pos_io and true_pos_err
        4: missing jump assumed between pos_io and pos_err
        5: broken weld assumed between pos_io and pos_err
        -1: could not determine

    Args: df, pos_err, error_treshold
    Returns: error_type, shift, pos_err
    
    '''
    ##############################################################################
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    #out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    #logger.info(out)
    logger.info(f'len(df), pos_err, pos_io, error_treshold: {len(df), pos_err, pos_io, error_treshold}')
    ##############################################################################
    
    df_bkp = df.copy()
    df = df.loc[pos_io:pos_err+30].copy()
    
    # temporal length of eos at error position
    dura_eos_err = df.loc[pos_err, 'dura_eos']

    ## try to find out shift using matching_sequence and matching_unique

    # calculate shift at error position - robustness not tested yet (30.11.2022)
    shift = matching_sequence(df, pos_err)
    if shift == 100:
        # try opposite direction
        shift = matching_sequence(df, pos_err, seq_len=5, max_iter=4, mode=1)


    # test shift in both directions severall times 
    tests = 0
    while(shift == 100 and tests <= 6):
        mode = -1
        if mode==-1:    
            try:
                # searchpoint afterwards err_pos; negative direction
                shift = matching_sequence(df, pos_err+(tests*2), seq_len=5, max_iter=4, mode=-1)
            except:
                print('matching_sequence() fails')
        if mode==1:
            try:
                # searchpoint afterwards err_pos; positive direction
                shift = matching_sequence(df, pos_err+(tests*2), seq_len=5, max_iter=4, mode=1)
            except:
                print('matching_sequence() fails')

        tests += 1
        mode = mode*-1

    # calculate shift by single unique
    if shift == 100:
        try:
            shift_unique, idx_unique = matching_unique(df_bkp, pos_err, min_weld_len=5, error_treshold=0.05, ntimes=2, win=10)
            logger.info(f'shift_unique = {shift_unique}')
            if shift_unique != 100:
                shift = shift_unique
                logger.info(f'use shift by unique instead of shift by sequence: {shift_unique}')
        except:
            shift_unique = 100
            idx_unique = -1
    
    if shift == 100 and shift_unique == 100:
        try:
            shift_unique, idx_unique = matching_unique(df_bkp, pos_err, min_weld_len=3, error_treshold=0.05, ntimes=2, win=10)
            print(shift_unique)
            if shift_unique != 100:
                shift = shift_unique
                logger.info(f'use shift by unique instead of shift by sequence: {shift_unique}')
        except:
            shift_unique = 100
            idx_unique = -1

    # compare shift values
    # if (shift != 100) and (shift != shift_unique):
    #     print(f'WARNING: shift by sequence: {shift} does not match shift by unique: {shift_unique} at index: {idx_unique}')

    # TODO if no shift was found may try another shift finding method

    # check if potentially non measurable short welds occur before pos_err
    # only meaningfull if dataframe starting with last pos_io was entered in error_determination()
    # if true, then non measured welds are not present --> failure should be non measured jump
    sweld = swelds(df.loc[:pos_err])
    first_eos_sweld = sweld.index[0]
    logger.info(f'sweld count: {len(sweld)}. Indexes: {sweld.index}')

    # # calculate candidates for dura_eos_err in ttl values in between pos_io and pos_err by temporal length
    # candidates_sweld2err = df.loc[(df['dura_ttl'] < (error_treshold+1)*dura_eos_err) & (df['dura_ttl'] > (1-error_treshold)*dura_eos_err)].copy()
    # candidates_sweld2err = candidates_sweld2err.loc[first_eos_sweld:pos_err]

    ## calculate ttl-candidates for eos duration at error position (dura_eos_err) in ttl values by temporal length and error_treshold
    candidates = df.loc[(df['dura_ttl'] < (error_treshold+1)*dura_eos_err) & (df['dura_ttl'] > (1-error_treshold)*dura_eos_err)].copy()
    # in between pos_io and pos_err 
    candidates_io2err = candidates.loc[:pos_err]
    # in between first sweld and pos_err 
    candidates_sweld2err = candidates.loc[first_eos_sweld:pos_err]
    # from pos_err
    candidates_err2end = candidates.loc[pos_err:]

    logger.info(f'dura_eos_err: {dura_eos_err}. measured candidates count for this length: {len(candidates)}')

    if len(candidates) == 1:
        true_pos_err = candidates.index[0]
        shift_true_pos = true_pos_err - pos_err
        if shift_true_pos != shift:
            logger.info(f'WARNING: shift by unique candidate: {shift_true_pos} != shift: {shift}; shift will be overwritten!')
            shift = shift_true_pos
    
    logger.info(f'shift: {shift}')
    
    # shift null might be wrong
    # if shift == 0:
    #     return df_bkp

    if shift >= 100 and len(sweld != 0):
        # no shift found; swelds present in range; drop shortest
        df_new = del_shortest(df_bkp, pos_io, pos_err)
        err_move, df_chk = chk_err_move(pos_err, df_new)
        if err_move >= -1 or err_move == (-1 - pos_err):
            return df_chk

    ## 1 shift negativ: missing weld or missing jump in measurement
    
    if shift <= 0:
        # 1A:
        # unique match in temporal length between pos_io and pos_error indicates true position (ttl weld count < eos count)
        if len(candidates_io2err) == 1:
            # true position of error position
            true_pos_err = candidates_io2err.index[0]
            shift_true_pos = true_pos_err - pos_err
            if shift_true_pos != shift:
                logger.info(f'WARNING: shift by unique candidate before pos_err: {shift_true_pos} != shift: {shift}; shift will be overwritten!')
                shift = shift_true_pos
                # may abort here

            # position found, failure must be previous
            sweld = swelds(df.loc[:true_pos_err+1])
            # could be missing measurement of weld or missing measurement of jump
            # if shift < -1 then failure types could be combined ?!
            if len(sweld) == 0:
                # no swelds found - should be missing jump
                # Fehlenden sprung validieren? Größter absoluter fehler sollte prv oder next enstprechen bei gleichzeitig hohem rel fehler
                # nur sinnvoll mit welds > 0.042 (2*sampling_width)
                logger.info('no swelds found in range')
                df_missing_jumps = df.loc[((df['error_abs_ms'] < df['eosdiff_nxt']+(error_treshold*df['eosdiff_nxt'])) & (df['error_abs_ms'] > df['eosdiff_nxt']-(error_treshold*df['eosdiff_nxt'])) & df['dura_eos'] > 1)]
                df_missing_jumps = df_missing_jumps.loc[pos_io:pos_err+1]
                
                ## 3: true error position found and no swelds present --> missing jump assumed

            else:
                # should be sweld
                # how many? -> shift
                # test error of sweld --> if false: test missing jump --> if false: shift sequence and ignore values
                #print(f'ERROR_DETERMINATION: shift = {shift}. Sweld count = {len(sweld)}. Drop shortest!')
                
                df_new = del_shortest(df_bkp, pos_io, pos_err)
                err_move, df_chk = chk_err_move(pos_err, df_new)
                if err_move >= -1 or err_move == (-1 - pos_err):
                    return df_chk
                ## 1: true error position found and swelds are present --> missing weld assumed
                
        # 1B:
        # no unique match
        else:
            if len(sweld) == 0:
                # no swelds found - should be missing jump
                print('ERROR_DETERMINATION WARNING: No potentially non measurable short welds found (pos_io:pos_err)!')
                ## TODO either try already here or return guessed. try -> return if false -> save returnment of error_determination()
                
                ## 4: true error position not found and no swelds are present --> missing jump assumed
                return 4, shift, pos_err
            else:
                # should be sweld
                # how many? -> shift
                # test error of sweld --> plausibility
                # action for 
                #print(f'ERROR_DETERMINATION: shift = {shift}. Sweld count = {len(sweld)}. Drop shortest!')
                # TODO test sweld dropping
                ## 2: true error position not found and swelds are present --> missing jump assumed
                df_new = del_shortest(df_bkp, pos_io, pos_err)
                err_move, df_chk = chk_err_move(pos_err, df_new)
                if err_move >= -1 or err_move == (-1 - pos_err):
                    return df_chk
                
    ## 2 shift positive: must be broken weld (jump measured inside eos vector where no nominal jump is defined)
    
    # if shift is not found --> =100 --> function enters shift positive
    else:
        if shift == 100:
            return -1, shift, pos_err
        else:
            
            # TODO analog missing jump

            ## 5: broken weld
            return 5, shift, pos_err

    # if nothing clear, exit function find next valid shift. shift it. mark area as not trustfull or delete/drop it directly