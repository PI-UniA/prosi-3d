import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt


def unwarpProj(img, fname, imgpoints, scale=1):
    """
    Unwarps the image through rotation, flipping, Matrix Transformation (M) and saves it as a file.

    Args:
        img (Array): Array of the image to unwarp
        fname (str): Filename of the newly created image
        imgpoints (ArrayofArrays): Imagepoints of the corners
        scale=1 (float): Value to scale the image
    Returns:
        tuple containing

        - **flipped** (*Array*) – Flipped image
        - **fout** (*str*) – Outputpath name
        - **M** (*Array*) – Perspective Matrix
    """
    # shape (px)
    h, w = img.shape[:2]

    # corners
    cimg = pd.DataFrame(imgpoints[0][:, 0, :])
    cimg.columns = ['ximg', 'yimg']
    cimg = cimg * scale

    # edge points for unwarp
    num_x = 43
    leup = 0
    lelo = cimg.shape[0] - num_x
    riup = num_x - 1
    rilo = -1
    src = np.float32([cimg.iloc[leup].values,
                      (cimg.iloc[lelo].values),
                      (cimg.iloc[riup].values),
                      (cimg.iloc[rilo].values)])

    lens = np.zeros(4)
    lens[0] = cimg.iloc[riup].values[0] - cimg.iloc[leup].values[0]
    lens[1] = cimg.iloc[riup].values[0] - cimg.iloc[leup].values[0]
    lens[2] = cimg.iloc[lelo].values[1] - cimg.iloc[leup].values[1]
    lens[3] = cimg.iloc[rilo].values[1] - cimg.iloc[riup].values[1]
    print(f"lengths of upper edge: {lens[0]}; lower: {lens[1]}; left: {lens[2]}; right: {lens[3]}")

    # Unwarped must be square. Dimensions should not be greater then longest edge of found quadrangle. more precise would be use hypotenuse above
    x = lens.max()
    y = x
    # Offsets to show regions above and left besides in output image
    offsx = 100 * scale
    offsy = 500 * scale
    dst = np.float32([(0 + offsx, 0 + offsy),
                      (x + offsx, 0 + offsy),
                      (0 + offsx, y + offsy),
                      (x + offsx, y + offsy)])

    # M: transform matrix, Minv: the inverse
    M = cv2.getPerspectiveTransform(src, dst)
    # use cv2.warpPerspective() to warp your image to a top-down view
    warped = cv2.warpPerspective(img, M, (h, w), flags=cv2.INTER_LINEAR)
    rotated = cv2.rotate(warped, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)
    flipped = cv2.flip(rotated, 0)
    fout = fname.rsplit('.', 1)[0] + '_unwarp.tif'
    cv2.imwrite(fout, flipped)
    return flipped, fout, M


def chessCorners(img, fname, x=43, y=43):
    """
    Retrieves from an image with a chessboard the object- and imagepoints.

    Args:
        img (Array): Array of the chessboard image
        fname (str): Filename of the newly created image
        x (int, optional): Amount of chessboard columns, defaults to 43
        y (int, optional): Amount of chessboard rows, defaults to 43
    Returns:
        If chesscorners were found

        - **gray** (*Array*) – Grayscale version of the input image
        - **objpoints** (*ArrayofArrays*) – Object points
        - **imgpoints** (*ArrayofArrays*) – Image points

        If no chesscorners were found

        - **ret** (*int*) : 0
    """
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((x * y, 3), np.float32)
    objp[:, :2] = np.mgrid[0:x, 0:y].T.reshape(-1, 2)
    # Arrays to store object points and image points from all images
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    # chessboard_flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FILTER_QUADS + cv2.CALIB_CB_NORMALIZE_IMAGE
    chessboard_flags = 0

    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img.ndim == 2:
        gray = img.copy()
    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, (x, y), chessboard_flags)
    # If found, add object points, image points (after refining them)
    n = corners.shape[0]
    file = fname.rsplit('\\', 1)[-1]
    if ret == True:
        print(f'{n} corners found in {file}')
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        df_corners = pd.DataFrame(corners2[:, 0])
        df_corners.columns = ['x', 'y']
        pos = fname.rfind('.')
        f = fname[:pos] + '_corners.h5'
        df_corners.to_hdf(f, key='df', mode='w')
        imgpoints.append(corners)
        # Draw and display the corners

        cv2.drawChessboardCorners(img, (x, y), corners2, ret)
        f = fname[:pos] + '_corners.tif'
        cv2.imwrite(f, img)
        return gray, objpoints, imgpoints
    else:
        print(f'No corners could be found. Check preprocessing of input image.')
        return 0


def undistort(img, fname, objpoints, imgpoints, scale=1):
    """
    Obtains the intrinsic Camera Matrix and distortion coefficients.
    Transforms image to compensate for lens distortion and saves the new image in a file.

    Args:
        img (Array): Array of the image
        fname (str): Filename of the newly created image
        objpoints (ArrayOfArrays): Objectpoints
        imgpoints (ArrayOfArrays): Imagepoints
        scale=1 (float): Value to scale the image
    Returns:
        tuple containing

        - **undist** (*Array*) – Undistorted image
        - **fout** (*str*) – Undistorted file output path
        - **cameraMatrix** (*Array*) – Camera Matrix
        - **distCoeffs** (*Array*) – Distortion coefficients
    """
    if scale != 1:
        imgpoints[0] = imgpoints[0] * scale
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    retval, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img.shape[::-1], None,
                                                                         None)
    # images shape
    h, w = img.shape[:2]
    newCamMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, (w, h), 1, (w, h))

    undist = cv2.undistort(img, cameraMatrix, distCoeffs, None, newCamMatrix)
    x, y, w, h = roi
    undist = undist[y:y + h, x:x + w]
    fout = fname.rsplit('.', 1)[0] + '_undist.tif'
    cv2.imwrite(fout, undist)

    return undist, fout, cameraMatrix, distCoeffs
