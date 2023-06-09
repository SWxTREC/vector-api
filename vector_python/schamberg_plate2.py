import numpy as np


def schamberg_plate2(theta, nu, phi_o, Uinf, Tatm, m_gas, m_surface, Tw, htrhmFlag, set_acqs, accomm):
    # Boltzmann constant
    kb = 1.3806503e-23

    # angle of reflection measured from surface plane
    theta_out = np.abs(np.arccos(np.cos(theta)**nu))
    if np.isnan(theta_out):
        theta_out = np.pi/2

    # check for reflections back into the surface
    if theta_out < phi_o:
        phi_o = theta_out

    # beamwith function
    tmp = 2 * phi_o / np.pi
    PHI = ((1 - tmp**2) / (1 - 4 * tmp**2)) * (0.5 * np.sin(2 * phi_o) - tmp) / (np.sin(phi_o) - tmp)
    if np.isnan(PHI):
        phi_o = phi_o + 0.00001
        tmp = 2 * phi_o / np.pi
        PHI = ((1 - tmp**2) / (1 - 4 * tmp**2)) * (0.5 * np.sin(2 * phi_o) - tmp) / (np.sin(phi_o) - tmp)

    # mass ratio
    mu = m_gas / m_surface

    # accommodation coefficient (Goodman)
    if set_acqs == 0:
        accomm = np.abs(3.6 * mu * np.sin(theta) / ((1 + mu)**2))

    # rms thermal speed
    c = np.sqrt(2 * kb * Tatm / m_gas)

    # inverse of the speed ratio (Schamberg's c/U)
    s = c / Uinf

    # kinetic energy expressed in temperature
    Tin = m_gas * Uinf**2 / (3 * kb)

    # theta prime
    thetaP = (np.arcsin(np.sin(theta) / np.sqrt(1 + s**2)))

    # delta correction angle
    delta = np.arctan(s)
    CD1, CN1, CT1 = CDhyperthermal(PHI, theta, Uinf, accomm, nu, Tw, Tin)
    if htrhmFlag == 0:
        CD2, CN2, CT2 = CDhyperthermal(PHI, theta + delta, Uinf, accomm, nu, Tw, Tin)
        CD3, CN3, CT3 = CDhyperthermal(PHI, theta - delta, Uinf, accomm, nu, Tw, Tin)
        CD4, CN4, CT4 = CDhyperthermal(PHI, thetaP, Uinf, accomm, nu, Tw, Tin)

        # drag coefficient (Joule Gas Approximation)
        CD = (1/3) * np.sqrt(1 + s**2) * (np.sqrt(1 + s**2) * CD1 +
                                             0.5 * (CD2 +
                                                    CD3) +
                                             CD4)

        CNRM = (1/3) * np.sqrt(1 + s**2) * (np.sqrt(1 + s**2) * CN1 +
                                              0.5 * (CN2 +
                                                     CN3) +
                                              CN4)

        CTAN = (1/3) * np.sqrt(1 + s**2) * (np.sqrt(1 + s**2) * CT1 +
                                              0.5 * (CT2 +
                                                     CT3) +
                                              CT4)
    if htrhmFlag == 1:
        CD = CD1
        CNRM = CN1
        CTAN = CT1

    return CD, CNRM, CTAN


def CDhyperthermal(PHI, theta, Vr, accomm, nu, Tw, Tin):
    Vout = Vr * np.sqrt(1 + accomm * (Tw / Tin - 1))

    # because this is hyperthermal, negative incoming angles should be neglected
    if theta < 0:
        CDinf = 0
        CNinf = 0
        CTinf = 0
        return CDinf, CNinf, CTinf

    # angle of reflection measured from surface plane
    theta_out = np.abs(np.arccos(np.cos(theta)**nu))
    if np.isnan(theta_out):
        theta_out = np.pi/2

    if np.sin(theta) == 0 or np.cos(theta) == 0:
        theta = theta + np.finfo(float).eps

    CNinf = -2 * np.abs(np.sin(theta)**2 * (1 + PHI * (Vout / Vr) * (np.sin(theta_out) / np.sin(theta))))
    CTinf = np.abs(2 * np.sin(theta) * np.cos(theta) * (1 - PHI * (Vout / Vr) * (np.cos(theta_out) / np.cos(theta))))
    CDinf = CTinf * np.cos(theta) - CNinf * np.sin(theta)

    return CDinf, CNinf, CTinf
