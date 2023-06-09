def DSMC_surface2(filename, TRI, pX, pY, pZ, hflag):
    # Open file for writing
    with open(filename, 'wt') as fid:
        # Data properties
        num_TR, _ = TRI.shape
        num_PT, = pX.shape
        
        # Write header
        if hflag:
            fid.write(f'{1}\n')  # Number of surfaces
            fid.write(f'{num_TR}\n')  # Number of points
        
        # Write triangle vertices one triangle per line
        for k in range(num_TR):
            INDXa = TRI[k, 0]
            INDXb = TRI[k, 1]
            INDXc = TRI[k, 2]
            Xplt = [pX[INDXa], pX[INDXb], pX[INDXc]]
            Yplt = [pY[INDXa], pY[INDXb], pY[INDXc]]
            Zplt = [pZ[INDXa], pZ[INDXb], pZ[INDXc]]
            
            # This becomes the TRS array in most instances
            fid.write('%.16f %.16f %.16f %.16f %.16f %.16f %.16f %.16f %.16f\n' % (
                Xplt[0], Yplt[0], Zplt[0], Xplt[1], Yplt[1], Zplt[1], Xplt[2], Yplt[2], Zplt[2])
            )

    # File closed automatically