import math

def schamberg_sphere(nu, phi_o, Uinf, Tatm, m_gas, m_surface, Tw, htrhmFlag, set_acqs, accomm):
    # Constants
    kb = 1.3806503e-23

    # Beamwidth function PHI
    tmp = 2 * phi_o / math.pi
    PHI = ((1 - tmp ** 2) / (1 - 4 * tmp ** 2)) * (0.5 * math.sin(2 * phi_o) - tmp) / (math.sin(phi_o) - tmp)

    if math.isnan(PHI):
        phi_o = phi_o + 0.00001
        tmp = 2 * phi_o / math.pi
        PHI = ((1 - tmp ** 2) / (1 - 4 * tmp ** 2)) * (0.5 * math.sin(2 * phi_o) - tmp) / (math.sin(phi_o) - tmp)

    # Mass ratio
    mu = m_gas / m_surface

    # Accommodation coefficient
    if not set_acqs:
        accomm = abs(3.6 * mu / ((1 + mu) ** 2))

    # RMS thermal speed
    c = math.sqrt(3 * kb * Tatm / m_gas)

    # Inverse of the speed ratio
    s = c / Uinf

    # Kinetic energy expressed in temperature
    Tin = m_gas * Uinf ** 2 / (3 * kb)

    CDinf = CD_hyperthermal(PHI, Uinf, accomm, nu, Tw, Tin)

    if htrhmFlag == 1:
        CD = CDinf

    if htrhmFlag == 0:
        CD = CD_nonhyperthermal(s, CDinf)

    return CD

# Definite integral
def I1(nu):
    if nu == 1:
        I1_eval = 1 / 4
    elif nu == 500:
        I1_eval = 1 / 3
    return I1_eval

# Hyperthermal drag coefficient
def CD_hyperthermal(PHI, Vr, accomm, nu, Tw, Tin):
    Vout = Vr * math.sqrt(1 + accomm * (Tw / Tin - 1))
    f_of_nu = 2 * (I1(nu) - (1 / (nu + 3)))
    CDinf = 2 * (1 + PHI * (Vout / Vr) * f_of_nu)
    return CDinf

# Nonhyperthermal drag coefficient approximation
def CD_nonhyperthermal(s, CDinf):
    CDfmf = ((2 + math.sqrt(1 + s ** 2)) / 3) * math.sqrt(1 + s ** 2) * CDinf
    return CDfmf
