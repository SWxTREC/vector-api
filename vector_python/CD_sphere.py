import numpy as np

from vector_python.sentman import sentman

def CD_sphere(Vt, NO_DENS, Tatm, Tw, accom):
    # constants
    mO = 2.6560178e-26  # atomic oxygen mass (~16 amu) [kg]
    mO2 = mO * 2
    mN2 = 4.6528299e-26  # molecular nitrogen mass [kg]
    mHe = 6.6465e-027
    mH = 1.6737e-027

    MASS_MAT = [mN2, mO2, mO, mHe, mH]
    RHO_MAT = MASS_MAT * NO_DENS
    RhoTot = np.dot(MASS_MAT, NO_DENS)
    CDpart = np.zeros(5)
    dCDpart = np.zeros(5)

    # scan atomic masses
    for km in range(5):
        if NO_DENS[km] == 0:  # skip zero number densities
            continue
        CD, _, _, _ = sentman(0, Tatm, Tw, accom, 0, Vt, MASS_MAT[km], 'sphere', -1)
        CDpart[km] = CD
        # XXX where does this come from?
        # TODO: Fill this in properly
        dCDpart[km] = derviCDsphere(Tatm, Tw, accom, Vt, MASS_MAT[km])  # partial derivative

    CDL = np.dot(CDpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    dCDL = np.dot(dCDpart, RHO_MAT) / RhoTot

    COEFS = np.array([0, CDL, 0])  # placeholders for future

    return COEFS, dCDL