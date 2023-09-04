import glob
import os
import pandas as pd
import numpy as np
import itertools
import cv2
from tqdm import tqdm

def eosCorners(path, n=43, lay=1):
    '''
    Find x,y values for corners of chessboard job.
    Read first layer file 'eosprint_layer00001.h5' and if not existant run readDf() and df2Layers_hdf() to create layer files from openjz.txt file.
    Calculate coordinates and save in file eoscorners.h5
    Args: path to openjobfile, nominal number of cornes which can be found
    Returns: corner coordinates
    '''
    eostxt = path + R'\*.openjz.txt'
    eostxt = glob.glob(eostxt)
    if len(eostxt) != 1:
        print(f'Warning: found eostxt file count is {len(eostxt)}')
    eostxt = eostxt[0]
    
    vecdir = path + '\\vec'
    layer = vecdir + '\\' + "eosprint_layer" + str(lay).zfill(5) + ".h5"

    if not os.path.isfile(layer):
        # if file is not present then run readDf and df2Layers_hdf. if so use first layer in vec
        print(f'{layer} not existant. Try to create.')
        df, layers, _ = readDf(eostxt)
        _ = df2Layers_hdf(df, layers, vecdir)
        if os.path.isfile(layer):
            print('Success.')
        else:
            print('Cannot create file.')
        
    chess = pd.read_hdf(layer)

    fname = path + R'\eoscorners.h5'

    # use exposure 1 or 10
    eos = chess.loc[(chess.exposureType == 10)].drop_duplicates()
    eos = eos.sort_values(by=['x_mm', 'y_mm'])
    eos = eos.astype(float)
    # + - 1 avoids if error by scanner corrections
    left = eos.x_mm.min() + 1
    right = eos.x_mm.max() - 1
    low = eos.y_mm.min() + 1
    high = eos.y_mm.max() - 1
    # filter in chesspoints area
    eos = eos.loc[((eos.x_mm < right) & (eos.y_mm < high) & (eos.x_mm > left) & (eos.y_mm > low))].copy()
    eos.reset_index(drop=True, inplace=True)
    total = int(len(eos)/n/2)
    eos['x_corner'] = 0
    eos['y_corner'] = 0
    for j in range(total):
        for i in range(n):
            line = j*2*n+i
            eos.x_corner.loc[line] = eos.x_mm.loc[line+n] + (eos.x_mm.loc[line] - eos.x_mm.loc[line+n])/2
            eos.y_corner.loc[line] = eos.y_mm.loc[line+n] + (eos.y_mm.loc[line] - eos.y_mm.loc[line+n])/2
    eos = eos.loc[eos.x_corner != 0]
    eos = eos.drop((['x_mm', 'y_mm', 'exposureType', 'partId']), axis = 1)
    print(f"Found intersection points: {eos.shape}")
    eos.to_hdf(fname, key='df', mode='w')
    return eos, chess

def unwarpProj(img, fname, imgpoints, scale=1, num_x=43):
    # shape (px)
    h, w = img.shape[:2]
    
    # corners
    cimg = pd.DataFrame(imgpoints[0][:,0,:])
    cimg.columns = ['ximg', 'yimg']
    cimg = cimg*scale

    ## NEED TO BE CORRECTED DEPENDING ON IMAGE PERSPEKTIVE, because findCorners starts always with smallest x-value
    # starting in left upper corner
    leup = 0
    lelo = cimg.shape[0] - num_x
    riup = num_x - 1
    rilo = -1

    # starting in right upper corner
    riup = 0
    leup = cimg.shape[0] - num_x
    rilo = num_x - 1
    lelo = -1

    src = np.float32([cimg.iloc[leup].values,
                    (cimg.iloc[lelo].values),
                    (cimg.iloc[riup].values),
                    (cimg.iloc[rilo].values)])

    lens = np.zeros(4)
    lens[0] = cimg.iloc[riup].values[0]-cimg.iloc[leup].values[0]
    lens[1] = cimg.iloc[riup].values[0]-cimg.iloc[leup].values[0]
    lens[2] = cimg.iloc[lelo].values[1]-cimg.iloc[leup].values[1]
    lens[3] = cimg.iloc[rilo].values[1]-cimg.iloc[riup].values[1]
    #print(f"lengths of upper edge: {lens[0]}; lower: {lens[1]}; left: {lens[2]}; right: {lens[3]}")

    # unwarped must be square. dimensions should not be greater then longest edge of found quadrangle. more precise would be use hypotenuse above
    x = lens.max()
    y = x
    # offsets to show regions above and left besides in output image
    # CAN CAUSE ISSUE IN chessCorners()
    offsx = 120*scale
    offsy = 500*scale
    dst = np.float32([(0+offsx, 0+offsy),
                    (x+offsx, 0+offsy),
                    (0+offsx, y+offsy),
                    (x+offsx, y+offsy)])
    
    # M: transform matrix, Minv: the inverse
    M = cv2.getPerspectiveTransform(src, dst)
    # use cv2.warpPerspective() to warp your image to a top-down view
    warped = cv2.warpPerspective(img, M, (h, w), flags=cv2.INTER_LINEAR)
    rotated = cv2.rotate(warped, cv2.ROTATE_90_COUNTERCLOCKWISE)
    flipped = cv2.flip(rotated, 0)
    fout = fname.rsplit('.', 1)[0] + '_unwarp.png'
    #cv2.imwrite(fout, flipped, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    return flipped, fout, M


def undistort(img, fname, objpoints, imgpoints, scale=1):
    #objpoints = objpoints*scale
    if scale != 1:
        imgpoints[0] = imgpoints[0]*scale
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    retval, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img.shape[::-1], None, None)
    # images shape
    h, w = img.shape[:2]
    newCamMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, (w,h), 1, (w,h))

    undist = cv2.undistort(img, cameraMatrix, distCoeffs, None, newCamMatrix)
    x, y, w, h = roi
    undist = undist[y:y+h, x:x+w]
    fout = fname.rsplit('.', 1)[0] + '_undist.png'
    cv2.imwrite(fout, undist, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    
    return undist, fout, cameraMatrix, distCoeffs


def chessCorners(img, fname, x=43, y=43):
    '''
    First function to run. Finds chessboard corners if possible
    Args: img, fname, x=43, y=43
    Returns: gray, objpoints, imgpoints
    '''
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((x*y,3), np.float32)
    objp[:,:2] = np.mgrid[0:x,0:y].T.reshape(-1,2)
    # Arrays to store object points and image points from all images
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    #chessboard_flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FILTER_QUADS + cv2.CALIB_CB_NORMALIZE_IMAGE
    chessboard_flags = 0

    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img.ndim == 2:
        gray = img.copy()
    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, (x,y), chessboard_flags)
    # If found, add object points, image points (after refining them)
    n = corners.shape[0]
    file = fname.rsplit('\\', 1)[-1]
    if ret == True:
        # refine found corners
        print(f'{n} corners found in {file}')
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
        df_corners = pd.DataFrame(corners2[:,0])
        df_corners.columns = ['x', 'y']
        pos = fname.rfind('.')
        f = fname[:pos] + '_corners.h5'
        df_corners.to_hdf(f, key='df', mode='w')
        imgpoints.append(corners)
        # Draw and display the corners
        # cv2.drawChessboardCorners(img, (x,y), corners2, ret)
        cv2.drawChessboardCorners(img, (x,y), corners2, ret)
        f = fname[:pos] + '_corners.png'
        cv2.imwrite(f, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        return gray, objpoints, imgpoints
    else:
        print(f'No cornes could be found. Check preprocessing of input image.')


def resize_img(imgpath, scale=0.25, max_px=2500):
    img = cv2.imread(imgpath, cv2.IMREAD_ANYDEPTH)
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if img.shape[0] > max_px or img.shape[1] > max_px:
        #gcd = gcd1(img.shape[0], img.shape[1])
        #math.gcd(img.shape[0], img.shape[1])
        img = cv2.resize(img, (0,0), fx=scale, fy=scale)
    else:
        scale=1
    return img, scale


def Points_and_correction(img, fname, x=43, y=43):
    '''
    find and apply corrections using a chessboard grid image
    
    '''
    # find corners
    img, objpoints, imgpoints = chessCorners(img, fname, x, y)
    # unwarp
    img, fname, M = unwarpProj(img, fname, imgpoints, scale=1, num_x=x)
    # find corners
    img, _, imgpoints2 = chessCorners(img, fname, x, y)
    # unproject
    img, fname, cameraMatrix, distCoeffs = undistort(img, fname, objpoints, imgpoints2)
    # find corners
    img, _, imgpoints3 = chessCorners(img, fname, x, y)
    return img, imgpoints, imgpoints2, imgpoints3, objpoints


def Apply_corrections_to_image(forig, scale, imgpoints, imgpoints2, objpoints, fromfile=R'C:\Users\ringel\Lokal\Python\Pixel-KOS\img\correction_cmos.h5', num_x=43):
    '''
    Apply_corrections_to_image(fpathorig, 4, 0, 0, 0, 1, 55) --> 55 Cornerpoints per axis (at the moment squared necessary), scaling 4 times of calibration data, calibration data from file
    Apply_corrections_to_image(fpathorig, 4, imgpoints, imgpoints2, objpoints, 0, 43) --> grid of 43 Cornerpoints and calibration data from entered directly

    Apply calibration values for perspektive (unwarp) and distortion to another image
    
    '''
    if os.path.isfile(fromfile):
        #path = fromfile.rsplit('\\img\\')[0]
        correction_cmos_rd = pd.read_hdf(fromfile, 'df')
        imgpoints = [correction_cmos_rd.imgpoints.values[0]]
        imgpoints2 = [correction_cmos_rd.imgpoints2.values[0]]
        imgpoints3 = [correction_cmos_rd.imgpoints3.values[0]]
        objpoints = [correction_cmos_rd.objpoints.values[0]]
        
    imgorig = cv2.imread(forig, cv2.IMREAD_ANYDEPTH)
    imgorig, fname, M = unwarpProj(imgorig, forig, imgpoints, scale, num_x)
    imgorig, fname, cameraMatrix, distCoeffs = undistort(imgorig, fname, objpoints, imgpoints2, scale)

def loopFilesInFolder_imgCorr(path, corrfile=R'C:\Users\ringel\Lokal\Python\Pixel-KOS\img\correction_cmos.h5', progress=True):
    files = [f.path for f in os.scandir(path)]
    print(f'{len(files)} files found.')
    if progress:
        for file in tqdm(files):
            Apply_corrections_to_image(file, 4, 0, 0, 0, corrfile, 55)
    else:
        for file in files:
            Apply_corrections_to_image(file, 4, 0, 0, 0, corrfile, 55)  


def matchCorners(path, scale=4):
    # import cornersfiles
    feos = path + R"\eoscorners.h5"
    fimg = glob.glob(path + R"\img\*_unwarp_undist_corners.h5")[0]
    print(f'feos: {feos}; fimg: {fimg}')
    ceos = pd.read_hdf(feos, 'df')
    cimg = pd.read_hdf(fimg, 'df')

    # apply scaling to pixels
    cimg = cimg*scale
    ceos.columns = ['xeos', 'yeos']
    cimg.columns = ['ximg', 'yimg']
    ceos.reset_index(drop=True, inplace=True)
    cimg.reset_index(drop=True, inplace=True)
    
    # calculate number of corner points along squared edge
    l = len(cimg)
    n = int(np.sqrt(l))
    # calculate index of pixel positions ipx which belong to positions of machine coordinates
    #ipx = l - (n*(((ics-1) % n)+1) - np.ceil(ics / n))

    ## !!!! Change depending on image perspektive. compare with unwarpProj()
    # alternative by sorting. eos coordinate system starts in left lower corners with x to the right and y upwards.
    # pixels start in upper left corner with y downwards and x to the right.
    # ceos['ipx'] = l - (n * (((ceos.index.copy()) % n) + 1) - np.ceil((ceos.index.copy() + 1) / n)) - 1
    # image pixel start in left upper - right upper - left lower - right lower  
    ceos['ipx'] = l - ((ceos.index.copy() % n + 1) * n - np.floor(ceos.index.copy() / n))
    # image pixel start in right upper - right lower - left upper - left lower  
    #ceos['ipx'] = np.ceil(ceos.index.copy() / n) * n - ceos.index.copy()

    corners = ceos.join(cimg, on='ipx', how='left')
    fout = path + R"\corr-corners.h5"
    corners.to_hdf(fout, key='df', mode='w')
    return corners


def extrapolate_full_built_field(xtable, ytable, plattformsize=250):
    #xtable.xeos.diff().mean(), ytable.yeos.diff().mean()
    #plattformsize = 250
    # calculate smallest / greatest pixelnumber
    addx0 = int(xtable.xeos.min()/xtable.xeos.diff().mean()+10)
    addx1 = int((plattformsize - xtable.xeos.max())/xtable.xeos.diff().mean()+10)
    addy0 = int(ytable.yeos.min()/ytable.yeos.diff().mean()+10)
    addy1 = int((plattformsize - ytable.yeos.max())/ytable.yeos.diff().mean()+10)
    #addx0, addx1, addy0, addy1

    def extrapolate(px, eos, start, end, plattformsize):
        fit = np.polyfit(px, eos , 1)
        line = np.poly1d(fit)
        if start > end:
            step = -1
        else:
            step = 1
        df = pd.DataFrame({'px': range(start, end, step)})
        df['eos'] = line(df.px)
        df = df.loc[(df.eos >= 0) & (df.eos <= plattformsize)]

        return df

    # add x smaller
    points = extrapolate(xtable.xpx, xtable.xeos, xtable.xpx.min()-addx0, xtable.xpx.min(), plattformsize)
    points.reset_index(drop=True, inplace=True)
    xtable.reset_index(drop=True, inplace=True)
    xtable.index = xtable.index + points.index[-1] + 1
    points.columns = ['xpx', 'xeos']
    # add x greater
    # vermeindlicher Fehler
    points2 = extrapolate(xtable.xpx, xtable.xeos, xtable.xpx.max()+1, xtable.xpx.max()+addx1, plattformsize)
    points2.reset_index(drop=True, inplace=True)
    points2.index = points2.index + xtable.index[-1] + 1
    points2.columns = ['xpx', 'xeos']

    xtable2 = pd.concat([points, xtable, points2])

    # add y smaller
    points = extrapolate(ytable.ypx, ytable.yeos, ytable.ypx.max()+addy0, ytable.ypx.max(), plattformsize)
    points.reset_index(drop=True, inplace=True)
    ytable.reset_index(drop=True, inplace=True)
    ytable.index = ytable.index + points.index[-1] + 1
    points.columns = ['ypx', 'yeos']
    # add y greater
    # vermeindlicher Fehler
    points2 = extrapolate(ytable.ypx, ytable.yeos, ytable.ypx.min()-1, ytable.ypx.min()-addy1, plattformsize)
    points2.reset_index(drop=True, inplace=True)
    points2.index = points2.index + xtable.index[-1] + 1
    points2.columns = ['ypx', 'yeos']

    ytable2 = pd.concat([points, ytable, points2])

    return xtable2, ytable2


def refering_pixel_table(corners, chessfieldwidth=4, tol=0.5):
    '''
    
    Calculate correlation tables between corner points and machine coordinates
    Args: corners
    Returns: xtable, ytable
    '''
    ## use mean px-value for same eos-values and list all corresponding integer x and y pixel values
    # Alternative: interpolate first and round afterwards to nominal pixels is may more accurate
    tmp_ximg = []
    tmp_yimg = []
    tmp_xeos = []
    tmp_yeos = []
    # x
    for i in range(int(round(corners.xeos.min(), 0)), int(round(corners.xeos.max(), 0)+chessfieldwidth), chessfieldwidth):
        tmp_xeos.append(corners.xeos.loc[(corners.xeos < i+tol) & (corners.xeos > i-tol)].median())
        #tmp_ximg.append(round(corners.ximg.loc[(corners.xeos < i+tol) & (corners.xeos > i-tol)].mean(), 0))
        tmp_ximg.append(corners.ximg.loc[(corners.xeos < i+tol) & (corners.xeos > i-tol)].mean())
    # y
    for i in range(int(round(corners.yeos.min(), 0)), int(round(corners.yeos.max(), 0)+chessfieldwidth), chessfieldwidth):
        tmp_yeos.append(corners.yeos.loc[(corners.yeos < i+tol) & (corners.yeos > i-tol)].median())
        #tmp_yimg.append(round(corners.yimg.loc[(corners.yeos < i+tol) & (corners.yeos > i-tol)].mean(), 0))
        tmp_yimg.append(corners.yimg.loc[(corners.yeos < i+tol) & (corners.yeos > i-tol)].mean())

    ## correlation of given points
    corrx = pd.DataFrame({'xeos': tmp_xeos, 'ximg': tmp_ximg})
    corry = pd.DataFrame({'yeos': tmp_yeos, 'yimg': tmp_yimg})

    ## Interpolation 
    xtable = pd.DataFrame({'xpx': range(int(np.ceil(corrx.ximg.min())), int(np.floor(corrx.ximg.max())+1), 1)})
    xtable['xeos'] = np.interp(xtable.xpx, corrx.ximg, corrx.xeos)
    ytable = pd.DataFrame({'ypx': range(int(np.floor(corry.yimg.max())), int(np.floor(corry.yimg.min())), -1)})
    # attention: indirect proportional - np.interp is not able to handle decreasing values
    # np.all(np.diff(1/corry.yimg) > 0)
    ytable['yeos'] = np.interp(1/ytable.ypx, 1/corry.yimg, corry.yeos)

    return xtable, ytable


def imgvalue(img, xpx, ypx):
    try:
        val = img[int(ypx), int(xpx)]
    except IndexError:
        val = np.nan
    return val


def findPixelByCoord(x, y, xtable, ytable, img, tol=0.05):
    '''
    Calculate pixel for machine coordinate
    do not use for generation of total time series by iteration - too slow
    Arguments: xtable, ytable (pixel and midpoint coordinate), x, y (coordinates), tol (tolerance for early filter for cpu saving; should at least equal pixel pitch)
    Returns: xpx, ypx
    '''
    # filter dataframe to speedup calculation
    filterx = xtable.loc[(xtable.xeos > (x - tol)) & (xtable.xeos < (x + tol))]
    filtery = ytable.loc[(ytable.yeos > (y - tol)) & (ytable.yeos < (y + tol))]
    # all possible pixels
    distances = pd.DataFrame(itertools.product(*[filterx.xeos, filtery.yeos]))
    distances.columns = ['xeos', 'yeos']
    # squared distances
    distances['dis2'] = np.power(x-distances.xeos, 2) + np.power(y-distances.yeos, 2)
    # nearest
    idx = distances.xeos.loc[distances.dis2 == distances.dis2.min()].index
    xfound = float(distances.loc[idx].xeos)
    yfound = float(distances.loc[idx].yeos)
    # get correlating pixel
    xpx = int(filterx.xpx.loc[filterx.xeos == xfound])
    ypx = int(filtery.ypx.loc[filtery.yeos == yfound])

    # pixel value
    try:
        val = img[xpx, ypx]
    except IndexError:
        val = np.nan

    return val
    #return xpx, ypx


def findPixelByCoordFlip(xtable, ytable, img, x, y, tol=0.05):
    '''
    Calculate pixel for machine coordinate
    Arguments: xtable, ytable (pixel and midpoint coordinate), x, y (coordinates), tol (tolerance for early filter for cpu saving; should at least equal pixel pitch)
    Returns: xpx, ypx
    '''
    # filter dataframe to speedup calculation
    filterx = xtable.loc[(xtable.xeos > (x - tol)) & (xtable.xeos < (x + tol))]
    filtery = ytable.loc[(ytable.yeos > (y - tol)) & (ytable.yeos < (y + tol))]
    # all possible pixels
    distances = pd.DataFrame(itertools.product(*[filterx.xeos, filtery.yeos]))
    distances.columns = ['xeos', 'yeos']
    # squared distances
    distances['dis2'] = np.power(x-distances.xeos, 2) + np.power(y-distances.yeos, 2)
    # nearest
    idx = distances.xeos.loc[distances.dis2 == distances.dis2.min()].index
    xfound = float(distances.loc[idx].xeos)
    yfound = float(distances.loc[idx].yeos)
    # get correlating pixel
    xpx = int(filterx.xpx.loc[filterx.xeos == xfound])
    ypx = int(filtery.ypx.loc[filtery.yeos == yfound])

    # pixel value
    try:
        val = img[xpx, ypx]
    except IndexError:
        val = np.nan

    return val
    #return xpx, ypx


def px_pitch_mcos():
    '''
    iterate all pixels and filter machine coordinate in xytime using pixel center point and pixel pitch
    
    '''