from math import erf

import numpy as np
from scipy.special import i0, i1


def sentman(alph, Ti, Tw, accom, epsil, V, m, shape, S):
    kb = 1.3806503e-23

    if S == -1:
        S = np.sqrt(np.sum(V**2) / (2 * kb * Ti / m))
    
    Tr = (m / (3 * kb)) * np.sum(V**2) * (1 - accom) + accom * Tw
    
    CD = 0

    if shape == 'surface':
        CA = ((np.cos(alph)**2) + 1 / (2 * S**2)) * (1 + erf(S * np.cos(alph))) + np.cos(alph) * np.exp(-S**2 * np.cos(alph)**2) / (S * np.sqrt(np.pi)) + np.sqrt(Tr / Ti) * ((np.sqrt(np.pi) / (2 * S)) * np.cos(alph) * (1 + erf(S * np.cos(alph)))) + np.exp(-S**2 * np.cos(alph)**2) / (2 * S**2)
        CN = np.sin(alph) * np.cos(alph) * (1 + erf(S * np.cos(alph))) + np.sin(alph) * np.exp(-S**2 * np.cos(alph)**2) / (S * np.sqrt(np.pi))
        CD = CN * np.sin(alph) + CA * np.cos(alph)
        CL = CN * np.cos(alph) - CA * np.sin(alph)
    
    elif shape == 'surfacespec':
        alph = -np.pi / 2 - alph
        CN = -(((1 + epsil) * S * np.sin(alph) / np.sqrt(np.pi) + 0.5 * (1 - epsil) * np.sqrt(Tr / Ti)) * np.exp(-S**2 * np.sin(alph)**2) + ((1 + epsil) * (0.5 + S**2 * np.sin(alph)**2) + (0.5 * (1 - epsil) * np.sqrt(Tr / Ti) * np.sqrt(np.pi) * S * np.sin(alph))) * (1 + erf(S * np.sin(alph)))) / S**2
        CA = -(((1 - epsil) * S * np.cos(alph) / np.sqrt(np.pi)) * (np.exp(-S**2 * np.sin(alph)**2) + np.sqrt(np.pi) * S * np.sin(alph) * (1 + erf(S * np.sin(alph))))) / S**2
        CD = np.abs(CN * np.sin(alph) + CA * np.cos(alph))
        CL = CN * np.cos(alph) - CA * np.sin(alph)
    
    elif shape == 'plate':
        CN = 0
        CA = 0
        alph = np.pi / 2 - alph
        CD = (2 * (1 - epsil * np.cos(2 * alph)) / (np.sqrt(np.pi) * S)) * np.exp(-S**2 * np.sin(alph)**2) + (np.sin(alph) / S**2) * (1 + 2 * S**2 + epsil * (1 - 2 * S**2 * np.cos(2 * alph))) * erf(S * np.sin(alph)) + ((1 - epsil) / S) * np.sqrt(np.pi) * np.sin(alph)**2 * np.sqrt(Tr / Ti)
        CL = (4 * epsil / (np.sqrt(np.pi) * S)) * np.sin(alph) * np.cos(alph) * np.exp(-S**2 * np.sin(alph)**2) + (np.cos(alph) / S**2) * (1 + epsil * (1 + 4 * S**2 * np.sin(alph)**2)) * erf(S * np.sin(alph)) + ((1 - epsil) / S) * np.sqrt(np.pi) * np.sin(alph) * np.cos(alph) * np.sqrt(Tr / Ti)
    
    elif shape == 'sphere':
        CN = 0
        CA = 0
        CD = ((2 * S**2 + 1) / (np.sqrt(np.pi) * S**3)) * np.exp(-S**2) + ((4 * S**4 + 4 * S**2 - 1) / (2 * S**4)) * erf(S) + ((2 * (1 - epsil) * np.sqrt(np.pi)) / (3 * S)) * np.sqrt(Tr / Ti)
        CL = 0
    
    elif shape == 'cylinder':
        Spar = S**2 * np.sin(alph)**2 / 2
        if Spar > 500:
            Spar = 500

        SF = 1
        # unscaled bessel functions
        besseli_0 = i0(Spar)
        besseli_1 = i1(Spar)
        CN = SF * (S * np.sqrt(np.pi) * np.sin(alph) * (2 * np.sin(alph)**2 + 1 / S**2) * np.exp(-Spar) * (besseli_0 + besseli_1) + (2 * np.sqrt(np.pi) / S) * np.sin(alph) * np.exp(-Spar) * besseli_0 + np.sqrt(Tr / Ti) * ((np.pi**1.5) / (2 * S)) * np.sin(alph))
        CA = SF * (2 * S * np.sqrt(np.pi) * np.sin(alph)**2 * np.cos(alph) * np.exp(-Spar) * (besseli_0 + besseli_1) + (2 * np.sqrt(np.pi) / S) * np.cos(alph) * np.exp(-Spar) * besseli_0)
        CD = CN * np.sin(alph) + CA * np.cos(alph)
        CL = CA * np.sin(alph) + CN * np.cos(alph)

    return CD, CL, CN, CA
