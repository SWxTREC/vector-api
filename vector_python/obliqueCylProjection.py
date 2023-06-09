import numpy as np


def obliqueCylProjection(D, L, pitch):
    # finds the oblique projection of a cylinder with angle pitch in radians
    if pitch == 0:
        pitch = np.nextafter(0, 1)  # Set pitch to smallest positive value
    if pitch < 0:
        pitch = np.abs(pitch)

    # ellipse parameters
    a = D / 2
    b = D * np.cos(pitch) / 2
    Aellipse = a * b * np.pi  # single ellipse area

    # sector angle
    Phi = np.arcsin(L * np.sin(pitch) / (2 * b))

    # sector area
    Asec = (a * b) * (np.arctan((b / a) * np.tan(np.pi / 2)) - np.arctan((b / a) * np.tan(Phi)))

    # triangle area
    y = L * np.sin(pitch) / 2
    base = 2 * y / np.tan(Phi)
    Atri = 0.5 * base * y

    # segment area
    Aseg = Asec - Atri

    # front cap oblique projection
    Afront = Aellipse

    # back cap oblique projection
    Aback = Aellipse
    if y < b:
        Aback = Aback - 2 * Aseg

    # find the projected midsection area - overlap
    Amid = L * np.sin(pitch) * D
    if y >= b:
        Amid = L * np.sin(pitch) * D - Aellipse
    if y < b:
        Amid = L * np.sin(pitch) * D - (Aellipse - 2 * Aseg)

    Atotal = Afront + Amid + Aback
    return Atotal
