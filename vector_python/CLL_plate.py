import math

def gamma_1(x):
    return 1 / (2 * math.sqrt(math.pi)) * (math.exp(-x**2) + math.sqrt(math.pi) * x * (1 + math.erf(x)))

def gamma_2(x):
    return 1 / (2 * math.sqrt(math.pi)) * (x * math.exp(-x**2) + (math.sqrt(math.pi) / 2) * (1 + 2 * x**2) * (1 + math.erf(x)))

def CLL_plate(alph, alpha_n, sigma_t, Uinf, Tatm, m_gas, Tw):
    # Beta is the angle-of-attack (units of radians)
    Beta = alph - math.pi / 2
    attk_angle = -math.pi / 2 - alph  # Transform to Bird's coordinates (angle of attack)

    # Universal gas constant
    R = 8.3145  # kg m^2 s^-2 mol^-1 K^-1

    # Avogadro's constant
    N_A = 6.0221409e23  # mol^-1

    # Molecular weight (m_gas in units of kg)
    m_molecular = m_gas * N_A  # kg/mol

    # Average normal velocity
    V_w = math.sqrt(math.pi * R * Tw / (2 * m_molecular))  # m/s

    V = Uinf  # m/s

    # Speed ratio
    s = V / math.sqrt(2 * R * Tatm / m_molecular)  # unitless

    # From Walker et al. 2014 paper, partial relationship between alpha_n and sigma_n
    sigma_n = 1 - math.sqrt(1 - alpha_n)

    # Parallel to the flow (i, x direction)
    CD = (2 / s) * (sigma_t * gamma_1(s * math.sin(Beta)) + ((2 - sigma_n) / s) * gamma_2(s * math.sin(Beta)) * math.sin(Beta) -
                    sigma_t * gamma_1(s * math.sin(Beta)) * (math.sin(Beta))**2 + sigma_n * (V_w / V) * gamma_1(s * math.sin(Beta)) * math.sin(Beta))

    # Perpendicular to the flow (j, y direction)
    CL = (2 / s) * (((2 - sigma_n) / s) * gamma_2(s * math.sin(Beta)) * math.cos(Beta) -
                    sigma_t * gamma_1(s * math.sin(Beta)) * math.sin(Beta) * math.cos(Beta) + sigma_n * (V_w / V) * gamma_1(s * math.sin(Beta)) * math.cos(Beta))

    # CN denotes the force normal to the plate
    CN = abs(CD * math.sin(attk_angle) + CL * math.cos(attk_angle)) * -1

    # CA is the force parallel (along the plate)
    CA = abs(CD * math.cos(attk_angle) - CL * math.sin(attk_angle))

    return CD, CL, CN, CA