import numpy as np
import matplotlib.pyplot as plt


def make_surface(filename, plt_flag, ViewDir):
    # converts .wrl filename into DSMC .txt format

    # open file for reading, it's a binary file
    with open(filename, 'r') as fid:
        # scan through header
        ID = 0
        while ID == 0 or ID == 3:
            line = fid.readline()
            ID = read_ID(line)
        ID = 0

        # scan points
        k = 1
        pX, pY, pZ = [], [], []
        while ID != 3:
            line = fid.readline()
            ID = read_ID(line)
            if ID == 3:
                break
            PTn, n = read_PTS(line)
            pX.extend(PTn[:, 0])
            pY.extend(PTn[:, 1])
            pZ.extend(PTn[:, 2])
            k = k + n

        # scan stuffing
        ID = 0
        while ID == 0 or ID == 3:
            line = fid.readline()
            ID = read_ID(line)
        line = fid.readline()

        # scan triangles
        ID = 0
        k = 1
        TRI = []
        while ID != 3:
            line = fid.readline()
            ID = read_ID(line)
            if ID == 3:
                break
            TRn, n = read_TR(line)
            TRI.extend(TRn)
            k = k + n


    if plt_flag:
        C = np.ones_like(pZ)
        fig = plt.gcf()
        ax = fig.add_subplot(111, projection='3d')
        color = plt.get_cmap('gray')(0.6)
        ax.plot_trisurf(pX, pY, pZ, triangles=TRI, color=color)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.view_init(ViewDir[1] - 90, ViewDir[0])
        # plt.show()

    TRI = np.array(TRI, dtype=int)
    pX = np.array(pX)
    pY = np.array(pY)
    pZ = np.array(pZ)
    return TRI, pX, pY, pZ


def read_ID(line):
    # id's the read line as either
    # 0-skip
    # 1-points
    # 2-triangles
    # 3-end bracket

    ID = 0
    id_char = line[0]

    if id_char == 'p' or id_char == 'I':
        id_str = line[0:5].strip()
        if id_str == 'point':
            ID = 1
        if id_str == 'Index':
            ID = 2

    if id_char == ']':
        ID = 3

    return ID


def read_PTS(line):
    # reads in coordinates and returns an N by 3 array
    PT_arr = np.array([np.fromstring(pts, sep=' ') for pts in line.strip(', \n').split(',')])
    n = PT_arr.size // 3
    PT = PT_arr.reshape((n, 3))
    return PT, n


def read_TR(line):
    # reads in triangle indices and returns an N by 3 array
    TR_arr = np.fromstring(line, sep=',')
    TR_arr = TR_arr[TR_arr != -1]
    n = TR_arr.size // 3
    TR = TR_arr.reshape((n, 3))
    return TR, n
