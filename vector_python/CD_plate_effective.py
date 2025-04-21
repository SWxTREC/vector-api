import numpy as np

from vector_python.sentman import sentman
from vector_python.CLL_plate import CLL_plate

def CD_plate_effective(alph, Vt, NO_DENS, MASS_MAT, Tatm, Tw, accom, ff, nu, phi_o, ms, set_acqs, A, material, GSI_model):
    # constants
    mO = 2.6560178e-26  # atomic oxygen mass (~16 amu) [kg]
    mO2 = mO * 2
    mN2 = 4.6528299e-26  # molecular nitrogen mass [kg]
    mHe = 6.6465e-027
    mH = 1.6737e-027

    RHO_MAT = MASS_MAT * NO_DENS
    RhoTot = np.dot(MASS_MAT, NO_DENS)
    CDpart = np.zeros(5)
    CNpart = np.zeros(5)
    CApart = np.zeros(5)

    # cross-sectional area
    # if alph == np.pi/2:  # prevent zero-crossing singularity
    #    alph = np.pi/2 - eps
    Acrs = np.abs(A * np.cos(alph))

    if material == 'SiO2':
        # range of SiO2 parameters
        incident_angles_data = 180 - np.array([30, 45, 60]) # degrees
        alpha_n_data = [0.98, 0.99, 0.98]
        sigma_t_data = [0.49, 0.81, 0.83]
        cos_frac_data = [0.97, 0.9, 0.79]
        alpha_data = [0.71, 0.61, 0.44]

    elif material == 'aluminum':
        # range of aluminum parameters
        incident_angles_data = 180 - np.array([30, 60]) # degrees
        alpha_n_data = [0.99, 0.98]
        sigma_t_data = [0.59, 0.85]
        cos_frac_data = [0.98, 0.88]
        alpha_data = [0.72, 0.55]

    elif material == 'Teflon':
        # range of teflon parameters
        incident_angles_data = 180 - np.array([30, 45, 60]) # degrees
        alpha_n_data = [0.99, 0.99, 0.98]
        sigma_t_data = [0.69, 0.81, 0.84]
        cos_frac_data = [0.96, 0.87, 0.76]
        alpha_data = [0.62, 0.50, 0.30]

    elif material == 'FR4':
        # range of FR4 parameters
        incident_angles_data = 180 - np.array([30, 45, 60]) # degrees
        alpha_n_data = [0.99, 0.99, 0.98]
        sigma_t_data = [0.59, 0.79, 0.85]
        cos_frac_data = [0.97, 0.93, 0.85]
        alpha_data = [0.68, 0.63, 0.52]

    # scan atomic masses
    for km in range(5):
        if NO_DENS[km] == 0:  # skip zero number densities
            continue

        if GSI_model == 3:
            # CLL quasi-specular reflection with alpha_n = 0.75, sigma_t = 0.9
            alpha_n = 0.75
            sigma_t = 0.9
            alpha_t = sigma_t * (2 - sigma_t)
            CDm, _, CNm, CAm = CLL_plate(np.pi - alph, alpha_n, sigma_t, Vt, Tatm, MASS_MAT[km], Tw)
            CNpart[km] = CNm
            CApart[km] = CAm
            CDpart[km] = CDm
            alpha_out = (alpha_n + alpha_t) / 2

        elif GSI_model == 4:
            # Extrapolated laboratory-derived GSI parameters weighted by surface area
            cos_frac = np.interp(np.degrees(np.pi - alph), incident_angles_data, cos_frac_data, left=0, right=1)
            accom = np.interp(np.degrees(np.pi - alph), incident_angles_data, alpha_data, left=0, right=1)
            alpha_n = np.interp(np.degrees(np.pi - alph), incident_angles_data, alpha_n_data, left=0, right=1)
            sigma_t = np.interp(np.degrees(np.pi - alph), incident_angles_data, sigma_t_data, left=0, right=1)

            [CDm, _, CNm, CAm] = sentman(np.pi - alph, Tatm, Tw, accom, 0, Vt, MASS_MAT[km], 'surfacespec', -1)
            [CDqs, CLqs, CNqs, CAqs] = CLL_plate(np.pi - alph, alpha_n, sigma_t, Vt, Tatm, MASS_MAT[km], Tw)

            cos_frac = min(1, max(0, cos_frac))
            accom = min(1, max(0, accom))
            alpha_n = min(1, max(0, alpha_n))
            sigma_t = min(1, max(0, sigma_t))

            CNpart[km] = (1 - cos_frac) * CNqs + cos_frac * CNm
            CApart[km] = (1 - cos_frac) * CAqs + cos_frac * CAm
            CDpart[km] = (1 - cos_frac) * CDqs + cos_frac * CDm

            alpha_cos = accom
            alpha_t = sigma_t * (2 - sigma_t)
            alpha_qs = (alpha_n + alpha_t) / 2
            alpha_out = cos_frac * alpha_cos + (1 - cos_frac) * alpha_qs

        else:
            # Sentman diffuse with incomplete and/or variable energy accommodation
            CDm, _, CNm, CAm = sentman(np.pi - alph, Tatm, Tw, accom, 0, Vt, MASS_MAT[km], 'surfacespec', -1)
            alpha_out = accom

            CNpart[km] = CNm
            CApart[km] = CAm
            CDpart[km] = CDm

    CDL = np.dot(CDpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    CAL = np.dot(CApart, RHO_MAT) / RhoTot  # recombine composite drag coefficient
    CNL = np.dot(CNpart, RHO_MAT) / RhoTot  # recombine composite drag coefficient

    CDtot = CDL * A / Acrs  # scaled coefficients

    COEFS = np.array([CAL, CDtot, CNL, Acrs, alpha_out])  # placeholders for future

    return COEFS