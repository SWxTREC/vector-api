import os

import numpy as np

from vector_python.CD_sphere2 import CD_sphere2
from vector_python.CD_plate_effective import CD_plate_effective
from vector_python.CD_cyl_effective import CD_cyl_effective
from vector_python.CD_triFile_effective import CD_triFile_effective
from vector_python.CD_RB_ENGINEERING4 import CD_RB_ENGINEERING4
from vector_python.geometry_wizard import geometry_wizard


def MAIN(obj_type, D, L, A, Phi, Theta, Ta, Va, n_O, n_O2, n_N2, n_He, n_H, EA_model, alpha, m_s, POSVEL, fnamesurf):
    # Constants
    set_acqs = 0  # quasi-specular
    ff = 0  # specular fraction
    nu = 0  # quasi specular "bending" parameter
    phi_o = 0  # quasi specular lobe width
    T_w = 300  # wall temperature
    mO = 2.6560178e-26  # atomic oxygen mass (~16 amu) [kg]
    mO2 = mO * 2
    mN2 = 4.6528299e-26  # molecular nitrogen mass [kg]
    mHe = 6.6465e-027
    mH = 1.6737e-027
    kb = 1.3806503e-23  # Boltzmann constant [J/K]
    Eb = 5.7  # eV
    Kf = 3e4
    Ko = 5e6
    Rcm = np.array([-0.01, 0.02, 0.01])  # position of center of mass from center of rectangular solid or sphere [m]
    ppscl = 1.25  # plotting constants
    offsetx = -0.05
    offsety = -0.05
    ppwidth = 8.5 * ppscl
    ppheight = 8.5 * ppscl

    # Input check
    rpv, cpv = POSVEL.shape

    # Multi point mode inputs
    if rpv > 0:
        Npts = rpv
        # Retrieve atmospheric properties

    # Single point mode inputs
    if rpv == 0:
        Npts = 1
        # Retrieve atmospheric properties
        NO_DENS = np.atleast_2d(np.array([n_N2, n_O2, n_O, n_He, n_H]))
        V_rel = np.array([Va])
        T_atm = np.array([Ta])

    # Energy Accommodation Coefficients
    MASS_MAT = np.array([mN2 * np.ones(Npts), mO2 * np.ones(Npts), mO * np.ones(Npts), mHe * np.ones(Npts), mH * np.ones(Npts)]).T
    m_b = np.sum(MASS_MAT * NO_DENS, axis=1) / np.sum(NO_DENS, axis=1)
    ro = mO * NO_DENS[:, 2]
    EA_set = EA_model
    if EA_model == 0:
        EA_set = alpha
    EA_vec, P_o, THETAsrf = CD_RB_ENGINEERING4(ro, m_b, T_atm, V_rel, m_s, EA_set, 1.00, Eb, Kf, Ko)
    alpha_out = EA_vec

    # CD computation
    CD = np.full((Npts, 1), -99, dtype=float)
    Aout = np.full((Npts, 1), A, dtype=float)
    Fcoef = np.full((Npts, 1), -99, dtype=float)

    # SURFACE MODEL (PLATE MODEL) GEOMETRY
    if obj_type == 4:  # geometry file
        ViewDir = [Phi, Theta]  # view direction
        dir_path = os.path.dirname(fnamesurf)
        # Get the name minus the extension
        fname = os.path.splitext(os.path.basename(fnamesurf))[0]
        tri_file = os.path.join(dir_path, 'TRIprops.txt')
        png_file = os.path.join(dir_path, f'geometry-{fname}.png')
        geometry_wizard(fnamesurf, tri_file, 0, 1, ViewDir)
        # delay import until needed when plotting the files
        import matplotlib.pyplot as plt
        plt.gcf()
        plt.set_cmap('gray')
        plt.xticks([])
        plt.yticks([])
        plt.gca().set_zticks([])
        plt.savefig(png_file, bbox_inches='tight', dpi=300)
        plt.close('all')

        TRS = np.loadtxt(tri_file)
        n_triangles = len(TRS)

    for k in range(Npts):
        # SPHERE
        if obj_type == 1:
            COEFS = CD_sphere2(V_rel[k], NO_DENS[k, :], T_atm[k], T_w, EA_vec[k], 0, 1, 0, m_s, 0)
            CD[k] = COEFS[1]
            Aout[k] = np.pi * D ** 2 / 4
            Fcoef[k] = COEFS[1] * Aout[k]

        # PLATE W/ ONE SIDE EXPOSED TO FLOW
        if obj_type == 2:
            COEFS = CD_plate_effective(Phi * np.pi / 180, V_rel[k], NO_DENS[k, :], T_atm[k], T_w, EA_vec[k], 0, 1, 0, m_s, 0, A)
            CD[k] = COEFS[1]
            Aout[k] = COEFS[3]
            Fcoef[k] = COEFS[1] * Aout[k]

        # CYLINDER
        if obj_type == 3:
            COEFS = CD_cyl_effective(V_rel[k], NO_DENS[k, :], T_atm[k], T_w, EA_vec[k], D, L, Phi * np.pi / 180)
            CD[k] = COEFS[1]
            Aout[k] = COEFS[3]
            Fcoef[k] = COEFS[1] * Aout[k]

        # SURFACE MODEL (PLATE MODEL) GEOMETRY
        if obj_type == 4:
            V_horz = V_rel[k] * np.cos(Phi * np.pi / 180)
            V_z = V_rel[k] * np.sin(Phi * np.pi / 180)
            V_x = V_horz * np.cos(Theta * np.pi / 180)
            V_y = V_horz * np.sin(Theta * np.pi / 180)
            V_plate_in = np.array([V_x, V_y, V_z])

            EPSILprops = np.zeros(n_triangles)
            COEFS = CD_triFile_effective(TRS, V_plate_in, NO_DENS[k, :], MASS_MAT[k, :], T_atm[k], T_w, EA_vec[k],
                                         EPSILprops, np.full(n_triangles, nu), np.full(n_triangles, phi_o),
                                         np.full(n_triangles, m_s), ff, Rcm.T, set_acqs)
            CD[k] = COEFS[1]
            Aout[k] = COEFS[3]
            Fcoef[k] = COEFS[1] * Aout[k]

    CD_status = 1

    return CD_status, CD, Aout, Fcoef, alpha_out
