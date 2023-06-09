import numpy as np

from vector_python.sentman import sentman

def CD_plate_effective(alph, Vt, NO_DENS, Tatm, Tw, accom, ff, nu, phi_o, ms, set_acqs, A):
    # constants
    mO = 2.6560178e-26  # atomic oxygen mass (~16 amu) [kg]
    mO2 = mO * 2
    mN2 = 4.6528299e-26  # molecular nitrogen mass [kg]
    mHe = 6.6465e-027
    mH = 1.6737e-027

    MASS_MAT = np.array([mH, mHe, mO, mN2, mO2])
    RHO_MAT = MASS_MAT * NO_DENS
    RhoTot = np.dot(MASS_MAT, NO_DENS)
    CDpart = np.zeros(5)
    CNpart = np.zeros(5)
    CApart = np.zeros(5)

    # Cosine Reflection only
    ff = 0
    CDqs = 0.0
    CAqs = 0.0
    CNqs = 0.0

    # cross-sectional area
    # if alph == np.pi/2:  # prevent zero-crossing singularity
    #    alph = np.pi/2 - eps
    Acrs = np.abs(A * np.cos(alph))

    # scan atomic masses
    for km in range(5):
        if NO_DENS[km] == 0:  # skip zero number densities
            continue
        CDm, _, CNm, CAm = sentman(np.pi - alph, Tatm, Tw, accom, 0, Vt, MASS_MAT[km], 'surfacespec', -1)
        # [CDqs,~,~]      = schamberg_sphere(nu,phi_o*pi/180,Vt,Tatm,MASS_MAT(km),ms,Tw,0,set_acqs,accom)  # <<<future capability
        CNpart[km] = (1 - ff) * CNm + ff * CNqs
        CApart[km] = (1 - ff) * CAm + ff * CAqs
        CDpart[km] = (1 - ff) * CDm + ff * CDqs

    CDL = np.dot(CDpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    CAL = np.dot(CApart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    CNL = np.dot(CNpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient

    CDtot = CDL * A / Acrs  # scaled coefficients

    COEFS = np.array([CAL, CDtot, CNL, Acrs])  # placeholders for future

    return COEFS