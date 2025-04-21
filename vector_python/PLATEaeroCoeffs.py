import numpy as np

from vector_python.schamberg_plate2 import schamberg_plate2
from vector_python.sentman import sentman
from vector_python.surface_geometry2 import surface_geometry2


def polygon_area(x, y):
    # Using shoelace formula
    correction = x[-1] * y[0] - y[-1]* x[0]
    main_area = np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:])
    return 0.5*np.abs(main_area + correction)

def PLATEaeroCoeffs(TRI, V, n, m, Ti, Tw, accom, EPSIL, nu, phi_o, m_surface, ff, Rcm, set_acqs, material, GSI_model):
    # given an arbitrary triangle file, computes the FMF drag of the entire
    # surface, cross-sectional area, and total force, for a single species assumes
    # ff is the fraction of quasi specular component
    # Rcm        =   cm offset from coordinate system
    #
    # example:
    # [CDXYZtotP,CDtotP,ArefFMF,FfmfTot,TQ] = PLATEaeroCoeffs(TRS,Vblk,n,m,Tatm,Tsurf,accom,TRSPROPS(:,3),1,m_gls*ones(n_triangles,1),0)

    # constants
    amu = 1.6605e-27
    Vmag = np.linalg.norm(V)
    ntri, _ = TRI.shape
    kb = 1.3806503e-23
    theta_therm = np.arctan(np.sqrt(2 * kb * Ti / m) / Vmag)

    # allocate storage vectors
    ACROSS = np.zeros(ntri)
    AFLAG = np.zeros(ntri)  # into 1, or out of 0 flow
    ASCALE = np.zeros(ntri)
    NVEC = np.zeros((ntri, 3))  # normal vector
    AVEC = np.zeros((ntri, 3))  # axial or along plate vector
    CNVEC = np.zeros(ntri)
    CAVEC = np.zeros(ntri)
    CDXYZ = np.zeros((ntri, 3))
    CDVEC = np.zeros(ntri)
    FXYZ = np.zeros((ntri, 3))
    CENTROIDS = np.zeros((ntri, 3))

    cos_frac_vals = np.zeros(ntri)
    accom_vals = np.zeros(ntri)
    alpha_n_vals = np.zeros(ntri)
    sigma_t_vals = np.zeros(ntri)

    if material == 'SiO2':
        # Range of SiO2 parameters
        incident_angles_data = [180 - angle for angle in [30, 45, 60]]  # degrees
        alpha_n_data = [0.98, 0.99, 0.98]
        sigma_t_data = [0.49, 0.81, 0.83]
        cos_frac_data = [0.97, 0.9, 0.79]
        alpha_data = [0.71, 0.61, 0.44]

    elif material == 'aluminum':
        # Range of aluminum parameters
        incident_angles_data = [180 - angle for angle in [30, 60]]  # degrees
        alpha_n_data = [0.99, 0.98]
        sigma_t_data = [0.59, 0.85]
        cos_frac_data = [0.98, 0.88]
        alpha_data = [0.72, 0.55]

    elif material == 'Teflon':
        # Range of Teflon parameters
        incident_angles_data = [180 - angle for angle in [30, 45, 60]]  # degrees
        alpha_n_data = [0.99, 0.99, 0.98]
        sigma_t_data = [0.69, 0.81, 0.84]
        cos_frac_data = [0.96, 0.87, 0.76]
        alpha_data = [0.62, 0.50, 0.30]

    elif material == 'FR4':
        # Range of FR4 parameters
        incident_angles_data = [180 - angle for angle in [30, 45, 60]]  # degrees
        alpha_n_data = [0.99, 0.99, 0.98]
        sigma_t_data = [0.59, 0.79, 0.85]
        cos_frac_data = [0.97, 0.93, 0.85]
        alpha_data = [0.68, 0.63, 0.52]


    # compute the cross-sectional (Across) and planform (Ascale) areas and the
    # angles of attack for each element
    # loop over triangles
    for k in range(ntri):
        N, Ct, A = getTRIprops(TRI[k, 0:9])  # triangle normal and center, and planform area
        PAM, _, _ = surface_geometry2(TRI[k, 0:9], N, V / Vmag, 0, 0)  # compute the projected area map of a single triangle
        CENTROIDS[k, 0:3] = Ct + Rcm
        dir_flag = np.sign(np.dot(V, N))  # +1 facing away from flow, -1 facing into flow
        XP = [PAM[0, 0], PAM[0, 2], PAM[0, 4]]
        YP = [PAM[0, 1], PAM[0, 3], PAM[0, 5]]
        ACROSS[k] = polygon_area(XP, YP)  # projected area of triangle
        AFLAG[k] = 0
        if dir_flag == -1:
            AFLAG[k] = 1
        ASCALE[k] = A

        # orientation
        cross_vec = np.cross(V, N)
        if np.linalg.norm(cross_vec) > np.finfo(float).eps:
            cross_vec = cross_vec / np.linalg.norm(cross_vec)
        if np.linalg.norm(cross_vec) <= np.finfo(float).eps:
            V = V + np.array([np.finfo(float).eps, -np.finfo(float).eps, np.finfo(float).eps])
            cross_vec = np.cross(V, N)  # added /norm(cross_vec)
        a_vec = np.cross(N, cross_vec)
        a_vec = a_vec / np.linalg.norm(a_vec)
        NVEC[k, 0:3] = N[0:3] / np.linalg.norm(N)
        AVEC[k, 0:3] = a_vec[0:3] / np.linalg.norm(a_vec)  # vector along the surface

        # compute the in-plane and out-of-plane coefficients
        alph = np.arccos(np.dot(V / Vmag, N / np.linalg.norm(N)))  # ?
        attk = -1 * dir_flag * np.arccos(np.dot(V / Vmag, a_vec))  # angle of attack

        # Function to calculate dotted_VN
        def calculate_dotted_VN(V, N):
            Vmag = np.linalg.norm(V)
            Nmag = np.linalg.norm(N)
            dotted_VN = np.arccos(np.dot(V / Vmag, N / Nmag))
            return dotted_VN

        dotted_VN = np.zeros(k)  # Initialize an array to store the results

        for i in range(k):
            dotted_VN[i] = calculate_dotted_VN(V, N)

        if GSI_model == 3:  # CLL quasi-specular reflection
            alpha_n = 0.75
            sigma_t = 0.9
            alpha_t = sigma_t * (2 - sigma_t)
            CDm, CLm, CNm, CAm = CLL_plate(alph, alpha_n, sigma_t, Vmag, Ti, m, Tw)
            CN = CNm
            CA = CAm
            CD = CDm
            alpha_out = (alpha_n + alpha_t) / 2

        elif GSI_model == 4:  # Extrapolated laboratory-derived GSI parameters
            cos_frac = np.interp(np.degrees(dotted_VN[k]), incident_angles_data, cos_frac_data, left=0, right=1)
            accom = np.interp(np.degrees(dotted_VN[k]), incident_angles_data, alpha_data, left=0, right=1)
            alpha_n = np.interp(np.degrees(dotted_VN[k]), incident_angles_data, alpha_n_data, left=0, right=1)
            sigma_t = np.interp(np.degrees(dotted_VN[k]), incident_angles_data, sigma_t_data, left=0, right=1)

            cos_frac = min(max(0, cos_frac), 1)
            accom = min(max(0, accom), 1)
            alpha_n = min(max(0, alpha_n), 1)
            sigma_t = min(max(0, sigma_t), 1)

            cos_frac_vals[k] = cos_frac
            accom_vals[k] = accom
            alpha_n_vals[k] = alpha_n
            sigma_t_vals[k] = sigma_t

            epsil = EPSIL(k)
            CDm, _, CNm, CAm = sentman(alph, Ti, Tw, accom, epsil, Vmag, m, 'surfacespec', -1)
            CDqs, CLqs, CNqs, CAqs = CLL_plate(alph, alpha_n, sigma_t, Vmag, Ti, m, Tw)
            # Calculate combined coefficients
            CN = (1 - cos_frac) * CNqs + cos_frac * CNm
            CA = (1 - cos_frac) * CAqs + cos_frac * CAm
            CD = (1 - cos_frac) * CDqs + cos_frac * CDm

            # Calculate alpha values
            alpha_cos = accom
            alpha_t = sigma_t * (2 - sigma_t)
            alpha_qs = (alpha_n + alpha_t) / 2
            alpha_out = cos_frac * alpha_cos + (1 - cos_frac) * alpha_qs

        else:  # Sentman diffuse with incomplete and/or variable energy accommodation
            epsil = EPSIL[k]
            CDm, _, CNm, CAm = sentman(alph, Ti, Tw, accom, epsil, Vmag, m, 'surfacespec', -1)
            alpha_out = accom

            # Set coefficients
            CN = CNm
            CA = CAm
            CD = CDm

        # store coefficients
        CNVEC[k] = CN
        CAVEC[k] = CA

        # compute force coefficients along the coordinate axes and along the
        # velocity vector
        CDXYZ[k, 0] = np.dot(NVEC[k, 0:3], [1, 0, 0]) * CN + np.dot(AVEC[k, 0:3], [1, 0, 0]) * CA
        CDXYZ[k, 1] = np.dot(NVEC[k, 0:3], [0, 1, 0]) * CN + np.dot(AVEC[k, 0:3], [0, 1, 0]) * CA
        CDXYZ[k, 2] = np.dot(NVEC[k, 0:3], [0, 0, 1]) * CN + np.dot(AVEC[k, 0:3], [0, 0, 1]) * CA
        CDVEC[k] = CD

    # compute the total cross-sectional area, Atot
    Atot = np.sum(ACROSS * AFLAG)

    # compute the total coefficients
    CDtot = np.sum(CDVEC * ASCALE) / Atot
    CDXYZtot = np.zeros((3, 1))
    CDXYZtot[0, 0] = np.sum(CDXYZ[0:, 0] * ASCALE) / Atot
    CDXYZtot[1, 0] = np.sum(CDXYZ[0:, 1] * ASCALE) / Atot
    CDXYZtot[2, 0] = np.sum(CDXYZ[0:, 2] * ASCALE) / Atot

    # compute element forces
    FXYZ[:, 0] = -0.5 * CDXYZ[0:, 0] * ASCALE * Vmag**2 * (n * m)
    FXYZ[:, 1] = -0.5 * CDXYZ[0:, 1] * ASCALE * Vmag**2 * (n * m)
    FXYZ[:, 2] = -0.5 * CDXYZ[0:, 2] * ASCALE * Vmag**2 * (n * m)
    TORQUES = np.cross(CENTROIDS, FXYZ, axis=1)
    TQtot = np.sum(TORQUES, axis=0)

    # compute the total force
    Ftot = -0.5 * Atot * CDXYZtot * Vmag**2 * (n * m)

    return CDXYZtot, CDtot, Atot, Ftot, TQtot, alpha_out


def getTRIprops(TRI):
    # given a row of the TRI matrix computes its normal (and center pos)

    # get vertices
    A = TRI[0:3]
    B = TRI[3:6]
    C = TRI[6:9]

    l1 = B - A
    l2 = C - A

    # right-handed normal?
    N = np.cross(l1, l2)

    # normalize each entry
    N /= np.linalg.norm(N)

    # triangle centroid
    Ct = np.sum([A, B, C], axis=0) / 3

    # triangle area
    base = l1
    hdir = np.cross(N, base)
    h = np.dot(l2, hdir) / np.linalg.norm(hdir)
    AA = 0.5 * np.linalg.norm(base) * h

    return N, Ct, AA
