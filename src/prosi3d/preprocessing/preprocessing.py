import logging, inspect, os
import pandas as pd
import numpy as np

from .utils import point_in_polygon, getPnts, getPolygons, shapePolygon, getZ, setcolor, chk_ascending, \
                    class_objects_to_dataframe

from .openjz import readDf, listpar_stl

from .io import filesInFolder_simple, folder2Files, listpar

from .layer import loopLayerMatchList, labelLayer_bindingError, errorLayer, reshapeLayerPartIds, reshape_eos_layer_file, \
                    correctContourExpTypes, assign_weld_speed, ttl2Welds

from .ttl import tJumpTTL, test_len_diff, update_ttlid_solved

from .debug import error_determination, solver_error_determination

from .welds import update_ttlid_nonjumps, corresponding_welds, corresponding_error, io_position, error_position, \
                    find_unique_welds_eos, matching_unique, swelds, rel_error, matching_sequence, del_shortest, \
                    chk_err_move, compare_temporal_weld_len, main_redefinelaserpathstarts, \
                    Weld, Weld_ttl, Part, ParameterSpeed

from .visualisation import vectors_view

from .camera import eosCorners, unwarpProj, undistort, chessCorners, resize_img, Points_and_correction, \
                    Apply_corrections_to_image, loopFilesInFolder_imgCorr, matchCorners, extrapolate_full_built_field, \
                    refering_pixel_table, imgvalue, findPixelByCoord, findPixelByCoordFlip, px_pitch_mcos

def main(path, layer):
    '''
    executed layerwise. opens unchanged eosprint_layer file. runs some corrections.
    create eosweld and ttlweld classes and run main_redefinelaserpathstarts(), whichs updates eoswelds
    restructure eoswelds to dataframe
    update t1 from calculated temporal length to timerow "weldend" time value
    write eos_print_corr file
    '''

    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    

    vecfile = '\\vec\\' + "eosprint_layer" + str(layer).zfill(5) + ".h5"
    logger.info(f'File in process: {vecfile}')

    eos_layer_file = pd.read_hdf(path + vecfile)
    eos_layer = reshape_eos_layer_file(eos_layer_file)
    eos_layer = correctContourExpTypes(eos_layer)
    eos_layer = assign_weld_speed(path, eos_layer)

    #eos_layer_file['exposureType'].value_counts()

    ## create class instances
    lsr_strt_jmp_len_jmp_strt_lsr_len = ttl2Welds(layer, path)
    ttlwelds = [Weld_ttl(*list(lsr_strt_jmp_len_jmp_strt_lsr_len.loc[id].values), id) for id in lsr_strt_jmp_len_jmp_strt_lsr_len.index]

    welds = [Weld(*list(eos_layer.loc[id].values), id) for id in eos_layer.index]
    welds = update_ttlid_nonjumps(welds)

    logger.info(f'measured welds (ttl): {len(ttlwelds)} of nominal welds (eosprint): {len(welds)}. Diff = {len(welds) - len(ttlwelds)}')
    logger.info(f'measured welds (ttl): {len(ttlwelds)} of nonjumpscorrected welds (eosprint): {welds[-1].ttlid}. Diff = {welds[-1].ttlid - len(ttlwelds)} (missing welds)')

    ## apply correction
    welds_updated, df, welds = main_redefinelaserpathstarts(welds, ttlwelds)

    ## transform to dataframe (reduce disk space in h5 file)
    df_from_obj = class_objects_to_dataframe(welds_updated)

    # drop NaNs in not deleted missing jumps (happens if they are neighbors)
    df_from_obj.drop(df_from_obj.t0.loc[df_from_obj.t0.isna() == True].index, inplace=True)

    # update t1
    df_from_obj = df_from_obj[['x0', 'y0', 'x1', 'y1', 'expType', 'prtId', 'x0_next', 'y0_next', 'speed', 'id', 'ttlid', 't0', 't1', 't1ttl']]
    df_from_obj['t1'] = df_from_obj['t1'] + df_from_obj['t0']

    # check ascending time values
    chk_ascending(df_from_obj['t0'])
    chk_ascending(df_from_obj['t1'])
    chk_ascending(df_from_obj['t1ttl'])

    ## save corrections
    a, b = vecfile.rsplit('_layer', 1)
    f = path + a + '_corr_layer' + b
    df_from_obj.to_hdf(f, key='df', mode='w')

    # return df to enable graphical check (barplot) eos vs ttl lengths
    return welds_updated, df #, df_from_obj, eos_layer

def loopMain(path, correction=0):
    '''
    Checks matching eosprint_layer and ch4raw_ files in subfolders of path and loops redefinelaserpathstarts() over those matching files.
    Use correction!=0 layer numbers do not equal, e.g. eosprint_layer00001 belongs to ch4raw_00003: correction=2
    
    Args: path, correction=0
    Returns: matches
    '''
    #print('>>>>>>>>>> ', inspect.currentframe().f_code.co_name, inspect.getargvalues(inspect.currentframe()).locals)
    
    # logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    # out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    # logger.info(out)

    eostxtfile, paramfile, jobfile, vecdir, ttldir, resdir, logdir, imgdir = folder2Files(path, 0)

    eoslayers = []
    ttllayers = []

    # check files by string and positions
    eosfiles = [f.path for f in os.scandir(vecdir)]
    for item in eosfiles:
        item = item.rsplit('eosprint_layer')[-1]
        item = item.rsplit('.', 1)[0]
        try:
            num = int(item)
        except:
            continue
        if item == str(num).zfill(5):
            eoslayers.append(num)

    ttlfiles = [f.path for f in os.scandir(ttldir)]
    for item in ttlfiles:
        item = item.rsplit('ch4raw_')[-1]
        item = item.rsplit('.', 1)[0]
        try:
            num = int(item)
        except:
            continue
        if item == str(num).zfill(5):
            ttllayers.append(num)

    eoslayers = np.array(eoslayers)
    ttllayers = np.array(ttllayers)+correction

    matches = eoslayers[np.isin(eoslayers,ttllayers)]
    #logger.info(f"Found correlating files: {list(matches)}")
    print(f"Found correlating files: {list(matches)}")

    for lay in matches:
        try:
            main(path, lay)
        except:
            #logger.info(f"ERROR: {lay} could not be processed. Check manually!")
            print(f"ERROR: {lay} could not be processed. Check manually!")
            pass