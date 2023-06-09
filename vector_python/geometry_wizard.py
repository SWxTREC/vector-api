from vector_python.make_surface import make_surface
from vector_python.DSMC_surface2 import DSMC_surface2

def geometry_wizard(file_in, file_out, hflag, plt_flag, ViewDir):
    # hflag - header flag
    TRI, X, Y, Z = make_surface(file_in, plt_flag, ViewDir)
    DSMC_surface2(file_out, TRI, X, Y, Z, hflag)

    # test
    # getArea(file_out)