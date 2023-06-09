import numpy as np

from vector_python.obliqueCylProjection import obliqueCylProjection
from vector_python.sentman import sentman

def CD_cyl(D, L, accomm, pitch, m, V_inf, T_inf, T_surf):
    # computes the drag coefficient of a capped cylinder (pitch in radians)

    ASC_cyl = np.abs(obliqueCylProjection(D, L, pitch))  # cross section of cylinder
    Aref_surf = np.pi * D**2 / 4

    CD_sides, CL_sides, _, _ = sentman(pitch, T_inf, T_surf, accomm, 0, V_inf, m, 'cylinder', -1)

    CD_capF, CL_capF, _, _ = sentman(pitch, T_inf, T_surf, accomm, 0, V_inf, m, 'surfacespec', -1)

    CD_capB, CL_capB, _, _ = sentman(pitch + np.pi, T_inf, T_surf, accomm, 0, V_inf, m, 'surfacespec', -1)

    CD_tot = (CD_capF * Aref_surf + CD_capB * Aref_surf + CD_sides * L * D / 2) / ASC_cyl
    CL_tot = (CL_capF * Aref_surf + CL_capB * Aref_surf + CL_sides * L * D / 2) / ASC_cyl

    return CD_tot, CL_tot, ASC_cyl