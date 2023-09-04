def readDf(path):
    """
    Reads txt-File exported via EOSPRINTAPI from *openjz.txt build-preview-file. Deletes non numeric numbers and calculates layerchanges.
    returns df: array with vector-tuple in rows and columns: x_mm, y_mm, exposureType, partId
    returns layers: list of layerchangelineindexes starting with change from 1 to 2
    returns vecdir where eosprint_layer files are stored via function df2layers
    
    Args: eostxtfilepath
    Returns: df, layers, vecdir
    """
    print('>>>>>>>>>> ', inspect.currentframe().f_code.co_name, inspect.getargvalues(inspect.currentframe()).locals)
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    logger.info(out)

    eostxtfile, _, jobfile, vecdir, _, _, logdir, _ = folder2Files(path)
    
    df = pd.read_csv(eostxtfile, sep=',', header=None, warn_bad_lines=True, skiprows=3)
    
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

    # logging
    fname = jobfile[:-8]
    delim = '\\'
    logger.info(f'Job: {fname.rsplit(delim,1)[-1]} has {len(layers)} layers with {len(df)/2} total vectors.')

    return df, layers, vecdir
