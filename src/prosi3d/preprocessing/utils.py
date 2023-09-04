import pandas as pd

def point_in_polygon(polygon, point):
    """
    Raycasting Algorithm to find out whether a point is in a given polygon.
    Performs the even-odd-rule Algorithm to find out whether a point is in a given polygon.
    This runs in O(n) where n is the number of edges of the polygon.
     *
    :param polygon: an array representation of the polygon where polygon[i][0] is the x Value of the i-th point and polygon[i][1] is the y Value.
    :param point:   an array representation of the point where point[0] is its x Value and point[1] is its y Value
    :return: whether the point is in the polygon (not on the edge, just turn < into <= and > into >= for that)
    """

    # A point is in a polygon if a line from the point to infinity crosses the polygon an odd number of times
    odd = False
    # For each edge (In this case for each point of the polygon and the previous one)
    i = 0
    j = len(polygon) - 1
    cnt = 0
    while i < len(polygon) - 1:
        i = i + 1
        # If a line from the point into infinity crosses this edge
        # One point needs to be above, one below our y coordinate
        # ...and the edge doesn't cross our Y corrdinate before our x coordinate (but between our x coordinate and infinity)

        if (((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) and (point[0] < (
                (polygon[j][0] - polygon[i][0]) * (point[1] - polygon[i][1]) / (polygon[j][1] - polygon[i][1])) +
                                                                            polygon[i][0])):
            # Invert odd
            odd = not odd
            cnt =+ 1
        j = i
    # If the number of crossings was odd, the point is in the polygon
    return odd, cnt

def getPnts(fname, pnts=4):
    '''
    Works at the moment only with
    
    '''
    f = open(fname, "r", encoding='UTF-8')
    #Point(X = 121.836, Y = 42.2803, Z = 1.36)
    list_x = []
    list_y = []
    i = 0
    for line in f:
        
        line = line.replace('\n','')
        x0 = line.find('X = ') + 4
        x1 = line.find(',', x0)
        x = line[x0:x1]
        y0 = line.find('Y = ') + 4
        y1 = line.find(',', y0)
        y = line[y0:y1]
        list_x.append(float(x))
        list_y.append(float(y))

        # read only first 4 points
        i += 1
        if i >= pnts:
            break
    # append first point to close polygon
    list_x.append(list_x[0])
    list_y.append(list_y[0])
    #d = {'x': list_x, 'y': list_y}
    df = pd.DataFrame()
    df['x'] = list_x
    df['y'] = list_y
    # points are not ordered in polygon representation (they are sorted by x and y)
    return df

def getPolygons(path, partlist):
    path = path + '\\stl\\'
    #files = filesInFolder_simple(path, typ='txt')
    polygonlist = []
    for part in partlist:
        txtfile = path + part.rsplit('.', 1)[0] + '.txt'
        polygon = shapePolygon(txtfile)
        polygonlist.append(polygon)
    
    return polygonlist


def shapePolygon(fname):
    '''
    iterative sorting by nearest next point to create a polygon with points in the right row.
    does not work for star-shaped areas -> then better use alphashape or sth else for sorting.
    '''
    pnts = getPnts(fname)
    # last point equals first point because of getPnts() to create a closed polygon
    idxlst = []
    df = pnts[1:-1].copy()
    for i in range(1, len(pnts) - 1, 1):
        # dataframe for distance calculation
        # nearest point is next point
        df.loc[:,'dx'] = df['x'] - pnts.loc[i-1, 'x']
        df.loc[:,'dy'] = df['y'] - pnts.loc[i-1, 'y']
        df['dx2'] = df['dx'].pow(2)
        df['dy2'] = df['dy'].pow(2)
        # distance from row in original list to
        df['dis'] = df[['dx2','dy2']].sum(axis=1).pow(1./2)
        #print(df['dis'].loc[df['dis'] == df['dis'].min()])
        foundidx = int(df.loc[df['dis'] == df['dis'].min()].index.values)
        idxlst.append(foundidx)
        df.drop(foundidx, inplace=True)
    idxlst = [0] + idxlst + [len(pnts) - 1]

    #apply index
    pnts.index = idxlst
    pnts.sort_index(inplace=True)

    polygon = []
    for row in pnts.itertuples():
        polygon.append((row.x, row.y))

    return polygon


def getZ(fname):
    '''
    Returns layer numbers of first layer above all binding errors of one stltxt file
    '''
    f = open(fname, "r", encoding='UTF-8')
    #Point(X = 121.836, Y = 42.2803, Z = 1.36)
    list_z = []
    i = 0
    for line in f:
        i += 1
        # dont read first 4 points
        if i <= 4:
            continue
        # delete line break
        line = line.replace('\n','')
        # find z coordinate
        z0 = line.find('Z = ') + 4
        z1 = line.find(')', z0)
        z = line[z0:z1]
        #floating number does not allow exact filtering -> use integers
        list_z.append(int(float(z)*1000))

    list_z = list(dict.fromkeys(list_z))
    list_z.sort()

    df = pd.DataFrame()
    df['z'] = list_z
    df['dz'] = df['z'].diff()
    cnts = df.dz.value_counts()
    # two values dominate (gap distance between error end to start and wise versa start to end). shorter distance is typically to the end of the error / missing layers
    zgaps = list((cnts.index[0], cnts.index[1]))
    zgaps = [int(item) for item in zgaps]
    zgaps.sort()
    # layer numbers of first layer above error
    z = list(df['z'].loc[df['dz'] == zgaps[0]].values/80)
    z = [int(item) for item in z]

    return z



def setcolor(expType):
    '''
    defines colors regarding eos exposureType number.
    called by function pfeile().
    
    Args: expType
    '''
    switch={
            # hatch
            0:'dodgerblue',         # Ansicht Bauteilaußenkante EOSprint
            # dunkler -> downskin, heller -> upskin
            1:'seagreen',           # down
            2:'mediumspringgreen',  # in
            3:'springgreen',        # up
            # contour
            4:'darkviolet',         # down
            5:'mediumorchid',       # in
            6:'magenta',            # up
            10:'violet',
            # edge
            7:'orangered',
            # support
            8:'dodgerblue',
            # jump
            9:'darkorange',
            11:'darkorange'
        }
    return switch.get(expType, 'black')

def chk_ascending(pandas_series):
    if ~pandas_series.is_monotonic:
        df = pd.DataFrame()
        df['diff1'] = pandas_series.diff()
        print(f"Not ascending cum_sums: {df.loc[pandas_series.diff() < 0].shape[0]}")
    print(f'Monotonic: {pandas_series.is_monotonic}')

def class_objects_to_dataframe(welds_updated):
    '''
    Helper function to convert list of objects to a 2d-representaion (pandas dataframe) using all attributes as columns and object as line.

    Args: list of objects
    Returns: pandas dataframe
    '''
    # create Dataframe from welds_updated objects
    cols = list(welds_updated[0].__dict__.keys())
    #cols = cols.append('duration_ms()')
    df = pd.DataFrame()
    for col in cols:
        df[col] = [getattr(weld, col) for weld in welds_updated]
    
    # additional values via methods
    # use t1 for temporal length and convert later to end time
    df['t1'] = [weld.duration_ms()/1000 for weld in welds_updated]
    # delete dropped short welds (ttlid == -1)
    df.drop(df.loc[df.ttlid == -1].index, inplace=True)
    return df
