"""
Accommodation coefficient calculation module for VECTOR.

This module provides different models for calculating energy accommodation
coefficients based on various physical models and surface conditions.
"""

import numpy as np
from typing import Union, Optional
from math import erf, sqrt, exp

from .constants import BOLTZMANN_CONSTANT, ATOMIC_MASS_UNIT, J_TO_EV, TORR_TO_PA
from .exceptions import CalculationError, ValidationError
from .atmosphere import AtmosphericComposition


def langmuir_k_model(temperature: float, 
                    binding_energy_ev: float,
                    slow_rate: float,
                    velocity: float,
                    fast_rate: float) -> float:
    """
    Calculate K parameter using Langmuir kinetic model.
    
    Args:
        temperature: Atmospheric temperature [K]
        binding_energy_ev: Binding energy [eV]
        slow_rate: Slow recombination rate parameter
        velocity: Velocity magnitude [m/s]
        fast_rate: Fast recombination rate parameter
        
    Returns:
        K parameter for accommodation calculation
    """
    if temperature < 0:
        temperature = np.finfo(float).eps
    
    binding_energy_j = binding_energy_ev / J_TO_EV
    
    if binding_energy_j < 0:
        binding_energy_j = np.finfo(float).eps
    if fast_rate < 5.0e3:
        fast_rate = 5.0e3
    
    atomic_oxygen_mass = 2.6560178e-26  # kg
    
    # Kinetic energy input
    xe = 0.5 * atomic_oxygen_mass * velocity**2
    
    # Calculate test section with overflow protection
    exponent_arg = 2 * sqrt(binding_energy_j * xe) / (BOLTZMANN_CONSTANT * temperature)
    if exponent_arg > 700:  # Prevent overflow (exp(700) is near float64 limit)
        test_section = 1.00e+306
    else:
        test_section = exp(exponent_arg)
    
    # Calculate SO_3 parameter with overflow protection
    sqrt_term = sqrt(np.pi * BOLTZMANN_CONSTANT * temperature * xe)
    erf_term1 = erf((sqrt(binding_energy_j) - sqrt(xe)) / sqrt(BOLTZMANN_CONSTANT * temperature))
    erf_term2 = erf(sqrt(xe / (BOLTZMANN_CONSTANT * temperature)))
    
    # Protect exponential calculations
    exp_arg1 = -(binding_energy_j + xe) / (BOLTZMANN_CONSTANT * temperature)
    exp_arg2 = binding_energy_j / (BOLTZMANN_CONSTANT * temperature)
    
    exp_term1 = exp(exp_arg1) if exp_arg1 > -700 else 0.0
    exp_term2 = exp(exp_arg2) if exp_arg2 < 700 else 1.00e+306
    
    numerator = (sqrt_term * (erf_term1 + erf_term2) +
                BOLTZMANN_CONSTANT * temperature * exp_term1 * (exp_term2 - test_section))
    
    # Protect denominator exponential calculation
    exp_arg3 = -xe / (BOLTZMANN_CONSTANT * temperature)
    exp_term3 = exp(exp_arg3) if exp_arg3 > -700 else 0.0
    
    denominator = (sqrt_term * (erf_term2 + 1) + 
                  BOLTZMANN_CONSTANT * temperature * exp_term3)
    
    so_3 = numerator / denominator
    
    k_model = so_3 * slow_rate + fast_rate
    
    # Handle numerical issues
    if np.isnan(k_model) or np.isinf(k_model):
        k_model = fast_rate
    
    return k_model


class AccommodationCalculator:
    """
    Calculator for energy accommodation coefficients using different models.
    
    This class provides various methods to calculate accommodation coefficients
    based on different physical models and surface conditions.
    """
    
    def __init__(self):
        """Initialize accommodation calculator."""
        pass
    
    def calculate_sesam_accommodation(self,
                                    atmosphere: AtmosphericComposition,
                                    velocity: float,
                                    temperature: float,
                                    surface_mass_amu: float,
                                    binding_energy_ev: float = 5.7,
                                    fast_rate: float = 3e4,
                                    slow_rate: float = 5e6,
                                    pressure_reduction: float = 1.0) -> Union[float, np.ndarray]:
        """
        Calculate accommodation coefficient using SESAM model.
        
        The SESAM (Surface Energy and Species Accommodation Model) calculates
        accommodation based on atomic oxygen interactions with the surface.
        
        Args:
            atmosphere: Atmospheric composition
            velocity: Velocity magnitude [m/s]
            temperature: Atmospheric temperature [K]
            surface_mass_amu: Surface mass [amu]
            binding_energy_ev: Surface binding energy [eV]
            fast_rate: Fast recombination rate parameter
            slow_rate: Slow recombination rate parameter
            pressure_reduction: Pressure reduction factor (e.g., 0.36 for GRACE)
            
        Returns:
            Energy accommodation coefficient(s) [0-1]
        """
        if not atmosphere.has_species('O'):
            raise CalculationError("SESAM model requires atomic oxygen in atmosphere")
        
        # Get atomic oxygen density
        atomic_oxygen_density = atmosphere.atomic_oxygen_density
        mean_molecular_mass = atmosphere.mean_molecular_mass
        
        # Calculate speed ratio for atomic oxygen
        atomic_oxygen_mass = 2.6560178e-26  # kg
        s_o = velocity * sqrt(atomic_oxygen_mass / (BOLTZMANN_CONSTANT * temperature))
        
        # Calculate drag coefficient for atomic oxygen
        cd_o = (((2 * s_o**2 + 1) / (sqrt(np.pi) * s_o**3)) * exp(-s_o**2) +
                ((4 * s_o**4 + 4 * s_o**2 - 1) / (2 * s_o**4)) * erf(s_o))
        
        # Calculate effective pressure
        p_o = (pressure_reduction * 0.5 * atomic_oxygen_density * cd_o * velocity**2 / TORR_TO_PA)
        
        # Mass ratio for surface accommodation
        mu = mean_molecular_mass / (surface_mass_amu * ATOMIC_MASS_UNIT)
        surface_accommodation = 2.434 * mu / ((1 + mu)**2)
        
        # Temperature for transition (empirical value)
        transition_temperature = 93.31  # K
        
        # Calculate K parameter using Langmuir model
        k_param = langmuir_k_model(transition_temperature, binding_energy_ev, 
                                  slow_rate, velocity, fast_rate)
        
        # Calculate surface coverage (theta)
        theta = k_param * p_o / (1 + k_param * p_o)
        
        # Final accommodation coefficient
        accommodation = theta + (1 - theta) * surface_accommodation
        
        return accommodation
    
    def calculate_goodman_accommodation(self,
                                      atmosphere: AtmosphericComposition,
                                      surface_mass_amu: float,
                                      incident_angle_rad: float = 0.0,
                                      shape: str = "sphere") -> Union[float, np.ndarray]:
        """
        Calculate accommodation coefficient using Goodman model.
        
        The Goodman model provides a simple mass-ratio based accommodation
        coefficient calculation.
        
        Args:
            atmosphere: Atmospheric composition
            surface_mass_amu: Surface mass [amu]
            incident_angle_rad: Incident angle [radians] (for plates)
            shape: Surface shape ("sphere" or "plate")
            
        Returns:
            Energy accommodation coefficient(s) [0-1]
        """
        mean_molecular_mass = atmosphere.mean_molecular_mass
        mu = mean_molecular_mass / (surface_mass_amu * ATOMIC_MASS_UNIT)
        
        if shape.lower() == "plate":
            # For plates, accommodation depends on incident angle
            accommodation = abs(3.6 * mu * np.sin(incident_angle_rad) / ((1 + mu)**2))
        else:
            # For spheres and other shapes
            accommodation = abs(3.6 * mu / ((1 + mu)**2))
        
        return accommodation
    
    def calculate_fixed_accommodation(self, value: float) -> float:
        """
        Return a fixed accommodation coefficient value.
        
        Args:
            value: Fixed accommodation coefficient [0-1]
            
        Returns:
            The input value (with validation)
        """
        if not (0 <= value <= 1):
            raise ValidationError("Accommodation coefficient must be between 0 and 1", 
                                "accommodation", value)
        
        return value
    
    def calculate_accommodation(self,
                              model_type: str,
                              atmosphere: AtmosphericComposition,
                              velocity: float,
                              temperature: float,
                              surface_mass_amu: float,
                              fixed_value: Optional[float] = None,
                              **kwargs) -> Union[float, np.ndarray]:
        """
        Calculate accommodation coefficient using specified model.
        
        Args:
            model_type: Model type ("sesam", "goodman", "fixed")
            atmosphere: Atmospheric composition
            velocity: Velocity magnitude [m/s]
            temperature: Atmospheric temperature [K]
            surface_mass_amu: Surface mass [amu]
            fixed_value: Fixed value (required for "fixed" model)
            **kwargs: Additional model-specific parameters
            
        Returns:
            Energy accommodation coefficient(s) [0-1]
        """
        model_type = model_type.lower().strip()
        
        if model_type == "sesam":
            return self.calculate_sesam_accommodation(
                atmosphere, velocity, temperature, surface_mass_amu, **kwargs)
        elif model_type == "goodman":
            return self.calculate_goodman_accommodation(
                atmosphere, surface_mass_amu, **kwargs)
        elif model_type == "fixed":
            if fixed_value is None:
                raise ValueError("fixed_value required for fixed accommodation model")
            return self.calculate_fixed_accommodation(fixed_value)
        else:
            raise ValueError(f"Unknown accommodation model: {model_type}. "
                           f"Available: sesam, goodman, fixed")