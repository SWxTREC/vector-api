import numpy as np

def surface_geometry2(TRI, TRInorm, V, rep_flag, red_flag):
    # r_T, c_T = TRI.shape
    r_T = 1  # only one triangle passed in at a time? Looping external
    Z = np.array([0, 0, 1], dtype=float)

    if np.linalg.norm(V) < 2 * np.finfo(float).eps:
        V = np.array([V[0] + 2 * np.finfo(float).eps, V[1] - 2 * np.finfo(float).eps, V[2] + 2 * np.finfo(float).eps], dtype=float)

    V_hat = V / np.linalg.norm(V)
    offst = -0.5

    PAM = np.zeros((r_T, 6), dtype=float)
    DRAW_PAM = np.zeros((3, 4), dtype=float)

    K_hat = np.cross(V_hat, Z)
    if np.linalg.norm(K_hat) < np.finfo(float).eps:
        Z = np.array([2 * np.finfo(float).eps, 2 * np.finfo(float).eps, 1 - 2 * np.finfo(float).eps], dtype=float)
        Z = Z / np.linalg.norm(Z)
        K_hat = np.cross(V_hat, Z)

    J_hat = np.cross(K_hat, V_hat)
    K_hat = K_hat / np.linalg.norm(K_hat)
    J_hat = J_hat / np.linalg.norm(J_hat)

    for k in range(r_T):
        if red_flag == 1:
            if np.dot(TRInorm[k, :3], V) > 0:
                continue

        PAM[k, 0] = np.dot(TRI[:3], J_hat)
        PAM[k, 1] = np.dot(TRI[:3], K_hat)
        PAM[k, 2] = np.dot(TRI[3:6], J_hat)
        PAM[k, 3] = np.dot(TRI[3:6], K_hat)
        PAM[k, 4] = np.dot(TRI[6:9], J_hat)
        PAM[k, 5] = np.dot(TRI[6:9], K_hat)

        if rep_flag == 1:
            DRAW_PAM[0, :4] = [PAM[k, 0], PAM[k, 2], PAM[k, 4], PAM[k, 0]]
            DRAW_PAM[1, :4] = [PAM[k, 1], PAM[k, 3], PAM[k, 5], PAM[k, 1]]
            DRAW_PAM[2, :4] = -offst

            # plt.plot(DRAW_PAM[0, :4], DRAW_PAM[1, :4])
            # plt.hold(True)

    # if rep_flag == 1:
    #     plt.axis('equal')
    #     plt.hold(False)

    return PAM, J_hat, K_hat

# Example usage:
# TRI = np.array(...)  # Define your input TRI matrix
# TRInorm = np.array(...)  # Define your input TRInorm matrix
# V = np.array(...)  # Define your velocity vector
# rep_flag = 1  # Set to 1 if you want to plot, 0 otherwise
# red_flag = 1  # Set to 1 to red flag faces facing away from the velocity, 0 to include all faces
# PAM, J_hat, K_hat = SURFACE_GEOMETRY2(TRI, TRInorm, V, rep_flag, red_flag)