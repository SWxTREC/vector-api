"""
Physical constants and configuration parameters for VECTOR drag calculations.

This module centralizes all physical constants, material properties, and
configuration parameters to improve maintainability and reduce magic numbers
throughout the codebase.
"""

from typing import Dict, Any
import numpy as np

# Physical Constants
BOLTZMANN_CONSTANT = 1.3806503e-23  # J/K
ATOMIC_MASS_UNIT = 1.6605e-27  # kg

# Atomic and molecular masses (kg)
class AtomicMasses:
    """Atomic and molecular masses in kg."""
    OXYGEN = 2.6560178e-26      # Atomic oxygen mass (~16 amu)
    OXYGEN_MOLECULE = OXYGEN * 2 # Molecular oxygen mass
    NITROGEN_MOLECULE = 4.6528299e-26  # Molecular nitrogen mass
    HELIUM = 6.6465e-27         # Helium mass
    HYDROGEN = 1.6737e-27       # Hydrogen mass

# Gas species indices for arrays
class GasSpecies:
    """Indices for gas species in density arrays."""
    N2 = 0
    O2 = 1
    OXYGEN = 2
    HELIUM = 3
    HYDROGEN = 4
    
    @classmethod
    def get_masses(cls) -> np.ndarray:
        """Get array of masses in the standard order."""
        return np.array([
            AtomicMasses.NITROGEN_MOLECULE,
            AtomicMasses.OXYGEN_MOLECULE,
            AtomicMasses.OXYGEN,
            AtomicMasses.HELIUM,
            AtomicMasses.HYDROGEN
        ])

# Default physical parameters
class DefaultPhysics:
    """Default physical parameters for calculations."""
    WALL_TEMPERATURE = 300.0  # K
    BINDING_ENERGY = 5.7      # eV
    FAST_RECOMBINATION_RATE = 3e4
    SLOW_RECOMBINATION_RATE = 5e6
    HYPERTHERMAL_FLAG = 0     # 0 = non-hyperthermal approximation
    
    # Schamberg model parameters
    SPECULAR_FRACTION = 0.0        # 0 = Sentman, 1 = Schamberg
    QUASI_SPECULAR_BENDING = 0.0   # nu parameter
    QUASI_SPECULAR_LOBE_WIDTH = 0.0  # phi_o in degrees
    
    # Center of mass offset from center of geometry [m]
    @staticmethod
    def get_center_of_mass_offset():
        return np.array([-0.01, 0.02, 0.01])

# Material properties
MATERIAL_PROPERTIES: Dict[str, Dict[str, Any]] = {
    'SiO2': {
        'incident_angles': [150, 135, 120],  # degrees (180 - [30, 45, 60])
        'alpha_n': [0.98, 0.99, 0.98],
        'sigma_t': [0.49, 0.81, 0.83],
        'cos_frac': [0.97, 0.9, 0.79],
        'accommodation': [0.71, 0.61, 0.44]
    },
    'aluminum': {
        'incident_angles': [150, 120],  # degrees (180 - [30, 60])
        'alpha_n': [0.99, 0.98],
        'sigma_t': [0.59, 0.85],
        'cos_frac': [0.98, 0.88],
        'accommodation': [0.72, 0.55]
    },
    'Teflon': {
        'incident_angles': [150, 135, 120],  # degrees (180 - [30, 45, 60])
        'alpha_n': [0.99, 0.99, 0.98],
        'sigma_t': [0.69, 0.81, 0.84],
        'cos_frac': [0.96, 0.87, 0.76],
        'accommodation': [0.62, 0.50, 0.30]
    },
    'FR4': {
        'incident_angles': [150, 135, 120],  # degrees (180 - [30, 45, 60])
        'alpha_n': [0.99, 0.99, 0.98],
        'sigma_t': [0.59, 0.79, 0.85],
        'cos_frac': [0.97, 0.93, 0.85],
        'accommodation': [0.68, 0.63, 0.52]
    }
}

# GSI Model types
class GSIModel:
    """Gas-Surface Interaction model types."""
    SESAM = -1                    # SESAM model
    FIXED = 0                    # Fixed accommodation coefficient
    GOODMAN = 2                  # Goodman model
    CLL_QUASI_SPECULAR = 3       # CLL quasi-specular with fixed parameters
    LABORATORY_DERIVED = 4       # Laboratory-derived GSI parameters

# Geometry types
class GeometryType:
    """Satellite geometry types."""
    SPHERE = 1
    PLATE = 2
    CYLINDER = 3
    CUSTOM = 4

# Unit conversions
TORR_TO_PA = 101325 / 760  # Torr to Pascal conversion factor
J_TO_EV = 6.24150974e18    # eV per Joule

# CLL model default parameters
class CLLDefaults:
    """Default parameters for CLL quasi-specular model."""
    ALPHA_N = 0.75  # Normal accommodation coefficient
    SIGMA_T = 0.9   # Tangential momentum accommodation coefficient

# Numerical tolerances
class Tolerances:
    """Numerical tolerances for calculations."""
    FLOAT_EPS = np.finfo(float).eps
    ZERO_VELOCITY_THRESHOLD = 2 * np.finfo(float).eps
    ANGLE_SINGULARITY_OFFSET = np.finfo(float).eps