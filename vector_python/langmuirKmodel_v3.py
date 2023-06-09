from math import erf

import numpy as np


def langmuirKmodel_v3(params, x, Kf_1):
    J2eV = 6.24150974e18  # eV per Joule
    Eb_1 = params[1] / J2eV
    Tatm_1 = params[0]
    Ko_1 = params[2]
    
    if Tatm_1 < 0:
        Tatm_1 = np.finfo(float).eps
    if Eb_1 < 0:
        Eb_1 = np.finfo(float).eps
    if Kf_1 < 5.0e3:
        Kf_1 = 5.0e3
    
    kb = 1.3806503e-23
    mO = 2.6560178e-26
    
    xe = 0.5 * mO * x ** 2  # J energy input
    
    test_section = np.exp(2 * np.sqrt(Eb_1 * xe) / (kb * Tatm_1))
    k_range = np.where(test_section == np.inf)[0]
    if len(k_range) > 0:
        test_section = 1.00e+306
    
    so_3 = (np.sqrt(np.pi * kb * Tatm_1 * xe) * (erf((np.sqrt(Eb_1) - np.sqrt(xe)) / np.sqrt(kb * Tatm_1)) + erf(np.sqrt(xe / (kb * Tatm_1)))) +
            kb * Tatm_1 * np.exp(-(Eb_1 + xe) / (kb * Tatm_1)) * (np.exp(Eb_1 / (kb * Tatm_1)) - test_section)) / \
           (np.sqrt(np.pi * kb * Tatm_1 * xe) * (erf(np.sqrt(xe / (kb * Tatm_1))) + 1) + kb * Tatm_1 * np.exp(-xe / (kb * Tatm_1)))
    
    K_model = so_3 * Ko_1 + Kf_1
    
    knaninf = np.where(np.isnan(K_model) | np.isinf(K_model))[0]
    if len(knaninf) > 0:
        K_model[knaninf] = Kf_1
    
    return K_model
