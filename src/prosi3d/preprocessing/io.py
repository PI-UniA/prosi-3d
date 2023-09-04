import os

def filesInFolder_simple(dir, typ='h5'):
    '''
    Helper function to select all files by file ending
    Args: dir, typ='h5'
    Returns: validfiles
    '''
    
    # files in folder
    files = [f.path for f in os.scandir(dir)]
    validfiles = []
    for file in files:
        # check file ending
        if file.rsplit('.', 1)[-1] == typ:
            validfiles.append(file)

    return validfiles


def folder2Files(path, stdprnt=1):
    """
    Use path as dir to project. Put inside *openjz.txt file, *.openjobfile and *_param.csv
    This functions helps to organize files in projectfolder by file-type
    Args: filepath
    Returns: eostxtfile, paramfile, jobfile, vecdir
    """
    print(path)
    files = [f.path for f in os.scandir(path)]
    #list_subfolders_with_paths = [f.path for f in os.scandir(path) if f.is_dir()]
    for fname in files:
        if fname[-11:] == '.openjz.txt':
            eostxtfile = fname
        if fname[-9:] == 'param.csv':
            paramfile = fname
        if fname[-8:] == '.openjob':
            jobfile = fname
    
    if 'eostxtfile' in locals():
        if stdprnt==1:
            print(eostxtfile)
    else:
        print('eostxtfile is not defined')
        eostxtfile = False
        
    if 'paramfile' in locals():
        if stdprnt==1:
            print(paramfile)
    else:
        print('paramfile is not defined')
        paramfile = False
        
    if 'jobfile' in locals():
        if stdprnt==1:
            print(jobfile)
    else:
        print('jobfile is not defined')
        jobfile = False
    
    vecdir = path + '\\vec'
    try:
        os.mkdir(vecdir)
    except:
        pass

    pdfdir = path + '\\pdf'
    try:
        os.mkdir(pdfdir)
    except:
        pass

    ttldir = path + '\\ttl'
    try:
        os.mkdir(ttldir)
        print(f'TTL Signal files missing. Put them in: {ttldir}')
    except:
        pass

    resdir = path + '\\res'
    try:
        os.mkdir(resdir)
    except:
        pass

    logdir = path + '\\log'
    try:
        os.mkdir(logdir)
    except:
        pass

    imgdir = path + '\\img'
    try:
        os.mkdir(logdir)
    except:
        pass

    return eostxtfile, paramfile, jobfile, vecdir, ttldir, resdir, logdir, imgdir


def dropFileDuplicates(lst, sep='_'):
    # remove file ending
    validfiles = [f.rsplit(sep, 1)[0] for f in lst]
    # remove file path
    validfiles = [f.rsplit('\\', 1)[1] for f in validfiles]
    # drop duplicates
    validfiles = list(dict.fromkeys(validfiles))
    return validfiles

def listpar(path):
    '''
    helper function to create csv with all occuring parameter names to then add DOE values manually to this file before calling vecTiming_hdf()

    Args: path
    Returns: <save empty parameter file with partnumbers (partId = partnumber+1) and assigned parameter names>
    '''
    
    #print('>>>>>>>>>> ', inspect.currentframe().f_code.co_name, inspect.getargvalues(inspect.currentframe()).locals)
    logger = logging.getLogger(inspect.currentframe().f_code.co_name)
    out = '>>>>>>>>>> ' + str(inspect.getargvalues(inspect.currentframe()).locals)
    logger.info(out)
    
    _, _, jobfile, _, _, _, _, _ = folder2Files(path,0)
    
    f = open(jobfile, 'r')
    df = f.readlines()
    partlist = []
    paramlist = []
    i = 0
    for line in df:
        if i == 0:
            vers = line.find('creator_version')
            logger.info(line[vers:])
                
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
    parlist.to_csv(jobfile[:-8] + '_param.csv', sep=';')
    logger.info(f'Parametersets: {len(paramlist)}, Teileanzahl: {len(partlist)}')
#    return paramlist, partlist