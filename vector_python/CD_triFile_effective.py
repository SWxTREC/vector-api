import numpy as np

from vector_python.PLATEaeroCoeffs import PLATEaeroCoeffs


def CD_triFile_effective(TRS, V_plate_in, NO_DENS, MASS_MAT, T_atm, T_w, accom, EPSILprops, NU, PHI_O, M_SURF, ff, Rcm, set_acqs):
    # constants
    mO = 2.6560178e-26  # atomic oxygen mass (~16 amu) [kg]
    mO2 = mO * 2
    mN2 = 4.6528299e-26  # molecular nitrogen mass [kg]
    mHe = 6.6465e-027
    mH = 1.6737e-027

    RHO_MAT = MASS_MAT * NO_DENS
    RhoTot = np.dot(MASS_MAT, NO_DENS)
    CDpart = np.zeros(5)
    CXpart = np.zeros(5)
    CYpart = np.zeros(5)
    CZpart = np.zeros(5)
    FXpart = np.zeros(5)
    FYpart = np.zeros(5)
    FZpart = np.zeros(5)
    TQXpart = np.zeros(5)
    TQYpart = np.zeros(5)
    TQZpart = np.zeros(5)

    # scan atomic masses
    for km in range(5):
        if NO_DENS[km] == 0:  # skip zero number densities
            continue

        [CDXYZtot, CDtot, Atot, Ftot, TQtot] = PLATEaeroCoeffs(TRS, V_plate_in, NO_DENS[km], MASS_MAT[km], T_atm, T_w, accom, EPSILprops, NU, PHI_O, M_SURF, ff, Rcm, set_acqs)

        # [CDqs,~,~] = schamberg_sphere(nu,phi_o*pi/180,Vt,Tatm,MASS_MAT(km),ms,Tw,0,set_acqs,accom);%<<<future capability
        CDpart[km] = CDtot
        CXpart[km] = CDXYZtot[0]
        CYpart[km] = CDXYZtot[1]
        CZpart[km] = CDXYZtot[2]
        FXpart[km] = Ftot[0]
        FYpart[km] = Ftot[1]
        FZpart[km] = Ftot[2]
        TQXpart[km] = TQtot[0]
        TQYpart[km] = TQtot[1]
        TQZpart[km] = TQtot[2]

    CDL = np.dot(CDpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    CXL = np.dot(CXpart, RHO_MAT) / RhoTot  # recombine composite CAx coefficient
    CYL = np.dot(CYpart, RHO_MAT) / RhoTot  # recombine composite CAy coefficient
    CZL = np.dot(CZpart, RHO_MAT) / RhoTot  # recombine composite CAz coefficient
    FXL = np.dot(FXpart, RHO_MAT) / RhoTot  # recombine composite FX coefficient
    FYL = np.dot(FYpart, RHO_MAT) / RhoTot  # recombine composite FY coefficient
    FZL = np.dot(FZpart, RHO_MAT) / RhoTot  # recombine composite FZ coefficient
    TQXL = np.dot(TQXpart, RHO_MAT) / RhoTot  # recombine composite TQX coefficient
    TQYL = np.dot(TQYpart, RHO_MAT) / RhoTot  # recombine composite TQY coefficient
    TQZL = np.dot(TQZpart, RHO_MAT) / RhoTot  # recombine composite TQZ coefficient

    CL1 = 0
    CL2 = 0

    COEFS = np.array([CL1, CDL, CL2, Atot, CXL, CYL, CZL, FXL, FYL, FZL, TQXL, TQYL, TQZL])  # placeholders for future

    return COEFS