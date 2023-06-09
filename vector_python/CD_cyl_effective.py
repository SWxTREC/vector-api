import numpy as np

from vector_python.CD_cyl import CD_cyl

def CD_cyl_effective(Vt, NO_DENS, Tatm, Tw, accom, D, L, pitch):
    # pitch is in radians
    # constants
    mO = 2.6560178e-26  # atomic oxygen mass (~16 amu) [kg]
    mO2 = mO * 2
    mN2 = 4.6528299e-26  # molecular nitrogen mass [kg]
    mHe = 6.6465e-027
    mH = 1.6737e-027

    MASS_MAT = np.array([mN2, mO2, mO, mHe, mH])
    RHO_MAT = MASS_MAT * NO_DENS
    RhoTot = np.dot(MASS_MAT, NO_DENS)
    CDpart = np.zeros(5)
    CLpart = np.zeros(5)
    dCDpart = np.zeros(5)

    # scan atomic masses
    for km in range(5):
        if NO_DENS[km] == 0:  # skip zero number densities
            continue
        CD, CL, Acs = CD_cyl(D, L, accom, pitch, MASS_MAT[km], Vt, Tatm, Tw)
        CDpart[km] = CD
        CLpart[km] = CL

    CDL = np.dot(CDpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    CLL = np.dot(CLpart, RHO_MAT) / RhoTot

    COEFS = np.array([0, CDL, CLL, Acs])  # placeholders for future
    
    return COEFS