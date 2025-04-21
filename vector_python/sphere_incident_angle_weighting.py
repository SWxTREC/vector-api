import math
import numpy as np

def sphere_incident_angle_weighting(r, material):
    # Constants
    inc_angle_res = 2.5  # degrees
    num_sections = int(90 / inc_angle_res) + 1

    # Initialize arrays to store data
    cos_frac_vals = np.zeros(num_sections)
    accom_vals = np.zeros(num_sections)
    alpha_n_vals = np.zeros(num_sections)
    sigma_t_vals = np.zeros(num_sections)
    across_vals = np.zeros(num_sections)
    ascale_vals = np.zeros(num_sections)

    for i in range(num_sections):
        inc_angle_bound1 = (i - 1) * inc_angle_res
        inc_angle_bound2 = i * inc_angle_res
        if i == num_sections - 1:
            mid_angle = 90
        else:
            mid_angle = inc_angle_bound1 + ((inc_angle_bound2 - inc_angle_bound1) / 2)

        # Material-specific data
        if material == 'SiO2':
            incident_angles_data = [30, 45, 60]  # degrees
            alpha_n_data = [0.98, 0.99, 0.98]
            sigma_t_data = [0.49, 0.81, 0.83]
            cos_frac_data = [0.97, 0.9, 0.79]
            alpha_data = [0.71, 0.61, 0.44]
        elif material == 'aluminum':
            incident_angles_data = [30, 60]  # degrees
            alpha_n_data = [0.99, 0.98]
            sigma_t_data = [0.59, 0.85]
            cos_frac_data = [0.98, 0.88]
            alpha_data = [0.72, 0.55]
        elif material == 'Teflon':
            incident_angles_data = [30, 45, 60]  # degrees
            alpha_n_data = [0.99, 0.99, 0.98]
            sigma_t_data = [0.69, 0.81, 0.84]
            cos_frac_data = [0.96, 0.87, 0.76]
            alpha_data = [0.62, 0.50, 0.30]
        elif material == 'FR4':
            incident_angles_data = [30, 45, 60]  # degrees
            alpha_n_data = [0.99, 0.99, 0.98]
            sigma_t_data = [0.59, 0.79, 0.85]
            cos_frac_data = [0.97, 0.93, 0.85]
            alpha_data = [0.68, 0.63, 0.52]

        cos_frac = np.interp(mid_angle, incident_angles_data, cos_frac_data, left=0, right=1)
        alpha_n = np.interp(mid_angle, incident_angles_data, alpha_n_data, left=0, right=1)
        sigma_t = np.interp(mid_angle, incident_angles_data, sigma_t_data, left=0, right=1)
        accom = np.interp(mid_angle, incident_angles_data, alpha_data, left=0, right=1)

        r1 = r * math.sin(math.radians(inc_angle_bound1))
        h1 = r * math.cos(math.radians(inc_angle_bound1))
        r2 = r * math.sin(math.radians(inc_angle_bound2))
        h2 = r * math.cos(math.radians(inc_angle_bound2))

        if i == num_sections - 1:  # back hemisphere
            SA = 2 * math.pi * r ** 2
            a_cross = math.pi * r ** 2
        else:  # spherical segment (ring)
            SA = 2 * math.pi * r * (h1 - h2)
            a_cross = math.pi * (r2 ** 2 - r1 ** 2)

        cos_frac_vals[i] = cos_frac
        accom_vals[i] = accom
        alpha_n_vals[i] = alpha_n
        sigma_t_vals[i] = sigma_t
        across_vals[i] = a_cross
        ascale_vals[i] = SA

    # Calculate weighted average parameters, weighted by surface area for segments on the front half of the sphere
    avg_cos_frac = np.sum(ascale_vals[:-1] * cos_frac_vals[:-1]) / np.sum(ascale_vals[:-1])
    avg_accom = np.sum(ascale_vals[:-1] * accom_vals[:-1]) / np.sum(ascale_vals[:-1])
    avg_alpha_n = np.sum(ascale_vals[:-1] * alpha_n_vals[:-1]) / np.sum(ascale_vals[:-1])
    avg_sigma_t = np.sum(ascale_vals[:-1] * sigma_t_vals[:-1]) / np.sum(ascale_vals[:-1])

    return avg_cos_frac, avg_accom, avg_alpha_n, avg_sigma_t
