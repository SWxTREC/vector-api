"""
Gas-Surface Interaction (GSI) models for VECTOR drag calculations.

This module provides different models for calculating gas-surface interaction
coefficients and drag forces on satellite surfaces.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, Optional
from math import erf, sqrt, pi, exp, sin, cos, asin as arcsin, acos as arccos, atan as arctan

from .constants import BOLTZMANN_CONSTANT, CLLDefaults
from .exceptions import GSIModelError


class GSIModel(ABC):
    """Abstract base class for gas-surface interaction models."""
    
    def __init__(self, name: str):
        """
        Initialize GSI model.
        
        Args:
            name: Name of the GSI model
        """
        self.name = name
    
    @abstractmethod
    def calculate_coefficients(self, 
                             angle: float,
                             velocity: float,
                             gas_temperature: float,
                             wall_temperature: float,
                             gas_mass: float,
                             accommodation: float,
                             **kwargs) -> Dict[str, float]:
        """
        Calculate drag and lift coefficients.
        
        Args:
            angle: Incident angle in radians
            velocity: Gas velocity magnitude [m/s]
            gas_temperature: Gas temperature [K]
            wall_temperature: Wall temperature [K]
            gas_mass: Gas molecular mass [kg]
            accommodation: Energy accommodation coefficient [0-1]
            **kwargs: Additional model-specific parameters
            
        Returns:
            Dictionary with coefficients (CD, CL, CN, CA)
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}')"


class SentmanModel(GSIModel):
    """
    Sentman gas-surface interaction model.
    
    This model provides analytical expressions for drag coefficients
    based on kinetic theory and different accommodation assumptions.
    """
    
    def __init__(self):
        super().__init__("Sentman")
    
    def calculate_coefficients(self,
                             angle: float,
                             velocity: float,
                             gas_temperature: float,
                             wall_temperature: float,
                             gas_mass: float,
                             accommodation: float,
                             shape: str = "surface",
                             specular_fraction: float = 0.0,
                             speed_ratio: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate Sentman model coefficients.
        
        Args:
            angle: Incident angle in radians
            velocity: Gas velocity magnitude [m/s]
            gas_temperature: Gas temperature [K]
            wall_temperature: Wall temperature [K]
            gas_mass: Gas molecular mass [kg]
            accommodation: Energy accommodation coefficient [0-1]
            shape: Surface shape ('surface', 'surfacespec', 'plate', 'sphere', 'cylinder')
            specular_fraction: Specular reflection fraction [0-1]
            speed_ratio: Optional speed ratio parameter
            
        Returns:
            Dictionary with coefficients
        """
        if speed_ratio is None:
            speed_ratio = sqrt(velocity**2 / (2 * BOLTZMANN_CONSTANT * gas_temperature / gas_mass))
        
        # Reflection temperature
        tr = (gas_mass / (3 * BOLTZMANN_CONSTANT)) * velocity**2 * (1 - accommodation) + accommodation * wall_temperature
        
        cd, cl, cn, ca = 0.0, 0.0, 0.0, 0.0
        
        if shape == 'surface':
            cd, cl, cn, ca = self._surface_coefficients(angle, speed_ratio, gas_temperature, tr)
        elif shape == 'surfacespec':
            cd, cl, cn, ca = self._surface_specular_coefficients(angle, speed_ratio, gas_temperature, tr, specular_fraction)
        elif shape == 'plate':
            cd, cl = self._plate_coefficients(angle, speed_ratio, gas_temperature, tr, specular_fraction)
        elif shape == 'sphere':
            cd = self._sphere_coefficient(speed_ratio, gas_temperature, tr, specular_fraction)
        elif shape == 'cylinder':
            cd, cl, cn, ca = self._cylinder_coefficients(angle, speed_ratio, gas_temperature, tr)
        else:
            raise GSIModelError(f"Unknown shape: {shape}")
        
        return {
            'CD': cd,
            'CL': cl,
            'CN': cn,
            'CA': ca
        }
    
    def _surface_coefficients(self, angle: float, s: float, ti: float, tr: float) -> tuple:
        """Calculate coefficients for general surface."""
        cos_alpha = cos(angle)
        sin_alpha = sin(angle)
        
        # Normal and axial coefficients
        ca = ((cos_alpha**2 + 1 / (2 * s**2)) * (1 + erf(s * cos_alpha)) + 
              cos_alpha * exp(-s**2 * cos_alpha**2) / (s * sqrt(pi)) +
              sqrt(tr / ti) * ((sqrt(pi) / (2 * s)) * cos_alpha * (1 + erf(s * cos_alpha))) +
              exp(-s**2 * cos_alpha**2) / (2 * s**2))
        
        cn = (sin_alpha * cos_alpha * (1 + erf(s * cos_alpha)) +
              sin_alpha * exp(-s**2 * cos_alpha**2) / (s * sqrt(pi)))
        
        cd = cn * sin_alpha + ca * cos_alpha
        cl = cn * cos_alpha - ca * sin_alpha
        
        return cd, cl, cn, ca
    
    def _surface_specular_coefficients(self, angle: float, s: float, ti: float, tr: float, epsilon: float) -> tuple:
        """Calculate coefficients for surface with specular reflection."""
        alpha = -pi / 2 - angle
        sin_alpha = sin(alpha)
        cos_alpha = cos(alpha)
        
        cn = -(((1 + epsilon) * s * sin_alpha / sqrt(pi) + 0.5 * (1 - epsilon) * sqrt(tr / ti)) * exp(-s**2 * sin_alpha**2) +
               ((1 + epsilon) * (0.5 + s**2 * sin_alpha**2) + (0.5 * (1 - epsilon) * sqrt(tr / ti) * sqrt(pi) * s * sin_alpha)) *
               (1 + erf(s * sin_alpha))) / s**2
        
        ca = -(((1 - epsilon) * s * cos_alpha / sqrt(pi)) *
               (exp(-s**2 * sin_alpha**2) + sqrt(pi) * s * sin_alpha * (1 + erf(s * sin_alpha)))) / s**2
        
        cd = abs(cn * sin_alpha + ca * cos_alpha)
        cl = cn * cos_alpha - ca * sin_alpha
        
        return cd, cl, cn, ca
    
    def _plate_coefficients(self, angle: float, s: float, ti: float, tr: float, epsilon: float) -> tuple:
        """Calculate coefficients for flat plate."""
        alpha = pi / 2 - angle
        sin_alpha = sin(alpha)
        cos_alpha = cos(alpha)
        
        cd = ((2 * (1 - epsilon * cos(2 * alpha)) / (sqrt(pi) * s)) * exp(-s**2 * sin_alpha**2) +
              (sin_alpha / s**2) * (1 + 2 * s**2 + epsilon * (1 - 2 * s**2 * cos(2 * alpha))) * erf(s * sin_alpha) +
              ((1 - epsilon) / s) * sqrt(pi) * sin_alpha**2 * sqrt(tr / ti))
        
        cl = ((4 * epsilon / (sqrt(pi) * s)) * sin_alpha * cos_alpha * exp(-s**2 * sin_alpha**2) +
              (cos_alpha / s**2) * (1 + epsilon * (1 + 4 * s**2 * sin_alpha**2)) * erf(s * sin_alpha) +
              ((1 - epsilon) / s) * sqrt(pi) * sin_alpha * cos_alpha * sqrt(tr / ti))
        
        return cd, cl
    
    def _sphere_coefficient(self, s: float, ti: float, tr: float, epsilon: float) -> float:
        """Calculate drag coefficient for sphere."""
        cd = (((2 * s**2 + 1) / (sqrt(pi) * s**3)) * exp(-s**2) +
              ((4 * s**4 + 4 * s**2 - 1) / (2 * s**4)) * erf(s) +
              ((2 * (1 - epsilon) * sqrt(pi)) / (3 * s)) * sqrt(tr / ti))
        
        return cd
    
    def _cylinder_coefficients(self, angle: float, s: float, ti: float, tr: float) -> tuple:
        """Calculate coefficients for cylinder."""
        try:
            from scipy.special import i0, i1
        except ImportError:
            raise GSIModelError("scipy is required for cylinder calculations but not available")
        
        sin_alpha = sin(angle)
        cos_alpha = cos(angle)
        
        s_par = s**2 * sin_alpha**2 / 2
        if s_par > 500:
            s_par = 500
        
        # Bessel functions
        bessel_i0 = i0(s_par)
        bessel_i1 = i1(s_par)
        
        cn = (s * sqrt(pi) * sin_alpha * (2 * sin_alpha**2 + 1 / s**2) * exp(-s_par) * (bessel_i0 + bessel_i1) +
              (2 * sqrt(pi) / s) * sin_alpha * exp(-s_par) * bessel_i0 +
              sqrt(tr / ti) * ((pi**1.5) / (2 * s)) * sin_alpha)
        
        ca = (2 * s * sqrt(pi) * sin_alpha**2 * cos_alpha * exp(-s_par) * (bessel_i0 + bessel_i1) +
              (2 * sqrt(pi) / s) * cos_alpha * exp(-s_par) * bessel_i0)
        
        cd = cn * sin_alpha + ca * cos_alpha
        cl = ca * sin_alpha + cn * cos_alpha
        
        return cd, cl, cn, ca


class CLLModel(GSIModel):
    """
    Cercignani-Lampis-Lord (CLL) gas-surface interaction model.
    
    This model accounts for incomplete accommodation in both normal
    and tangential momentum components.
    """
    
    def __init__(self):
        super().__init__("CLL")
    
    def calculate_coefficients(self,
                             angle: float,
                             velocity: float,
                             gas_temperature: float,
                             wall_temperature: float,
                             gas_mass: float,
                             accommodation: float,
                             alpha_n: float = CLLDefaults.ALPHA_N,
                             sigma_t: float = CLLDefaults.SIGMA_T,
                             shape: str = "plate") -> Dict[str, float]:
        """
        Calculate CLL model coefficients.
        
        Args:
            angle: Incident angle in radians
            velocity: Gas velocity magnitude [m/s]
            gas_temperature: Gas temperature [K]
            wall_temperature: Wall temperature [K]
            gas_mass: Gas molecular mass [kg]
            accommodation: Energy accommodation coefficient [0-1] (not used directly)
            alpha_n: Normal accommodation coefficient [0-1]
            sigma_t: Tangential momentum accommodation coefficient [0-1]
            shape: Surface shape ('plate' or 'sphere')
            
        Returns:
            Dictionary with coefficients
        """
        # Universal gas constant per unit mass
        r_specific = BOLTZMANN_CONSTANT / gas_mass  # J/(kg·K)
        
        # Average wall velocity
        v_w = sqrt(pi * r_specific * wall_temperature / 2)
        
        # Speed ratio
        s = velocity / sqrt(2 * r_specific * gas_temperature)
        
        # Calculate sigma_n from alpha_n
        sigma_n = 1 - sqrt(1 - alpha_n)
        
        if shape == "plate":
            cd, cl, cn, ca = self._plate_coefficients(angle, s, sigma_n, sigma_t, v_w, velocity)
        elif shape == "sphere":
            cd = self._sphere_coefficient(s, sigma_n, sigma_t, v_w, velocity)
            cl, cn, ca = 0.0, 0.0, 0.0
        else:
            raise GSIModelError(f"CLL model not implemented for shape: {shape}")
        
        return {
            'CD': cd,
            'CL': cl,
            'CN': cn,
            'CA': ca
        }
    
    def _gamma_1(self, x: float) -> float:
        """CLL gamma_1 function."""
        return (1 / (2 * sqrt(pi))) * (exp(-x**2) + sqrt(pi) * x * (1 + erf(x)))
    
    def _gamma_2(self, x: float) -> float:
        """CLL gamma_2 function."""
        return (1 / (2 * sqrt(pi))) * (x * exp(-x**2) + (sqrt(pi) / 2) * (1 + 2 * x**2) * (1 + erf(x)))
    
    def _plate_coefficients(self, angle: float, s: float, sigma_n: float, sigma_t: float, v_w: float, v: float) -> tuple:
        """Calculate CLL coefficients for flat plate."""
        beta = angle - pi / 2  # Transform angle
        attack_angle = -pi / 2 - angle
        
        sin_beta = sin(beta)
        cos_beta = cos(beta)
        
        # Parallel to flow (x direction)
        cd = (2 / s) * (sigma_t * self._gamma_1(s * sin_beta) + 
                       ((2 - sigma_n) / s) * self._gamma_2(s * sin_beta) * sin_beta -
                       sigma_t * self._gamma_1(s * sin_beta) * sin_beta**2 + 
                       sigma_n * (v_w / v) * self._gamma_1(s * sin_beta) * sin_beta)
        
        # Perpendicular to flow (y direction)
        cl = (2 / s) * (((2 - sigma_n) / s) * self._gamma_2(s * sin_beta) * cos_beta -
                       sigma_t * self._gamma_1(s * sin_beta) * sin_beta * cos_beta + 
                       sigma_n * (v_w / v) * self._gamma_1(s * sin_beta) * cos_beta)
        
        # Transform to normal/axial coordinates
        cn = abs(cd * sin(attack_angle) + cl * cos(attack_angle)) * -1
        ca = abs(cd * cos(attack_angle) - cl * sin(attack_angle))
        
        return cd, cl, cn, ca
    
    def _sphere_coefficient(self, s: float, sigma_n: float, sigma_t: float, v_w: float, v: float) -> float:
        """Calculate CLL drag coefficient for sphere."""
        cd = ((2 - sigma_n + sigma_t) / (2 * s**3) * 
              (((4 * s**4 + 4 * s**2 - 1) / (2 * s)) * erf(s) +
               ((2 * s**2 + 1) / sqrt(pi)) * exp(-s**2)) +
              (4 / 3) * sigma_n * (v_w / v))
        
        return cd


class SchambergModel(GSIModel):
    """
    Schamberg gas-surface interaction model.
    
    This model extends the Sentman model with quasi-specular reflection
    and includes hyperthermal and non-hyperthermal formulations.
    """
    
    def __init__(self):
        super().__init__("Schamberg")
    
    def calculate_coefficients(self,
                             angle: float,
                             velocity: float,
                             gas_temperature: float,
                             wall_temperature: float,
                             gas_mass: float,
                             accommodation: float,
                             nu: float = 1.0,
                             phi_o_deg: float = 0.0,
                             surface_mass: float = 1.0,
                             hyperthermal_flag: bool = True,
                             use_goodman_accommodation: bool = False,
                             shape: str = "plate") -> Dict[str, float]:
        """
        Calculate Schamberg model coefficients.
        
        Args:
            angle: Incident angle in radians  
            velocity: Gas velocity magnitude [m/s]
            gas_temperature: Gas temperature [K]
            wall_temperature: Wall temperature [K]
            gas_mass: Gas molecular mass [kg]
            accommodation: Energy accommodation coefficient [0-1]
            nu: Quasi-specular bending parameter
            phi_o_deg: Quasi-specular lobe width in degrees
            surface_mass: Surface mass for Goodman accommodation [amu]
            hyperthermal_flag: Use hyperthermal (True) or non-hyperthermal (False) formulation
            use_goodman_accommodation: Use Goodman accommodation model
            shape: Surface shape ('plate' or 'sphere')
            
        Returns:
            Dictionary with coefficients
        """
        phi_o = np.radians(phi_o_deg)
        
        # Beamwidth function PHI
        tmp = 2 * phi_o / pi
        if abs(1 - 4 * tmp**2) < 1e-10:  # Avoid division by zero
            phi_o += 1e-5
            tmp = 2 * phi_o / pi
        
        phi_func = ((1 - tmp**2) / (1 - 4 * tmp**2)) * (0.5 * sin(2 * phi_o) - tmp) / (sin(phi_o) - tmp)
        
        # Mass ratio and accommodation
        mu = gas_mass / (surface_mass * 1.6605e-27)  # Convert amu to kg
        
        if use_goodman_accommodation:
            if shape == "plate":
                accommodation = abs(3.6 * mu * sin(angle) / ((1 + mu)**2))
            else:
                accommodation = abs(3.6 * mu / ((1 + mu)**2))
        
        # RMS thermal speed and speed ratio
        c = sqrt(3 * BOLTZMANN_CONSTANT * gas_temperature / gas_mass)
        s = c / velocity
        
        # Kinetic energy expressed as temperature
        t_in = gas_mass * velocity**2 / (3 * BOLTZMANN_CONSTANT)
        
        if shape == "plate":
            cd, cl, cn, ca = self._plate_coefficients(angle, phi_func, velocity, accommodation, 
                                                    nu, wall_temperature, t_in, s, hyperthermal_flag)
        elif shape == "sphere":
            cd = self._sphere_coefficient(phi_func, velocity, accommodation, nu, 
                                        wall_temperature, t_in, s, hyperthermal_flag)
            cl, cn, ca = 0.0, 0.0, 0.0
        else:
            raise GSIModelError(f"Schamberg model not implemented for shape: {shape}")
        
        return {
            'CD': cd,
            'CL': cl,
            'CN': cn,
            'CA': ca
        }
    
    def _plate_coefficients(self, angle: float, phi_func: float, velocity: float, 
                          accommodation: float, nu: float, wall_temp: float, 
                          t_in: float, s: float, hyperthermal: bool) -> tuple:
        """Calculate Schamberg coefficients for flat plate."""
        # Angle of reflection measured from surface plane
        theta_out = abs(arccos(cos(angle)**nu))
        if np.isnan(theta_out):
            theta_out = pi / 2
        
        # Check for reflections back into surface (phi_o adjustment not used in this implementation)
        
        # Hyperthermal coefficients
        cd1, cn1, ct1 = self._hyperthermal_plate_coefficients(angle, phi_func, velocity, 
                                                             accommodation, nu, wall_temp, t_in)
        
        if not hyperthermal:
            # Non-hyperthermal corrections
            theta_p = arcsin(sin(angle) / sqrt(1 + s**2))
            delta = arctan(s)
            
            cd2, cn2, ct2 = self._hyperthermal_plate_coefficients(angle + delta, phi_func, velocity,
                                                                accommodation, nu, wall_temp, t_in)
            cd3, cn3, ct3 = self._hyperthermal_plate_coefficients(angle - delta, phi_func, velocity,
                                                                accommodation, nu, wall_temp, t_in)
            cd4, cn4, ct4 = self._hyperthermal_plate_coefficients(theta_p, phi_func, velocity,
                                                                accommodation, nu, wall_temp, t_in)
            
            # Non-hyperthermal corrections (Joule Gas Approximation)
            factor = (1/3) * sqrt(1 + s**2)
            cd = factor * (sqrt(1 + s**2) * cd1 + 0.5 * (cd2 + cd3) + cd4)
            cn = factor * (sqrt(1 + s**2) * cn1 + 0.5 * (cn2 + cn3) + cn4)
            ct = factor * (sqrt(1 + s**2) * ct1 + 0.5 * (ct2 + ct3) + ct4)
        else:
            cd, cn, ct = cd1, cn1, ct1
        
        cl = 0.0  # Not calculated for plates in this model
        ca = ct  # Tangential component becomes axial
        
        return cd, cl, cn, ca
    
    def _hyperthermal_plate_coefficients(self, angle: float, phi_func: float, velocity: float,
                                       accommodation: float, nu: float, wall_temp: float, t_in: float) -> tuple:
        """Calculate hyperthermal coefficients for plate."""
        if angle < 0:
            return 0.0, 0.0, 0.0
        
        v_out = velocity * sqrt(1 + accommodation * (wall_temp / t_in - 1))
        
        # Angle of reflection
        theta_out = abs(arccos(cos(angle)**nu))
        if np.isnan(theta_out):
            theta_out = pi / 2
        
        if sin(angle) == 0 or cos(angle) == 0:
            angle += 1e-10
        
        cn = -2 * abs(sin(angle)**2 * (1 + phi_func * (v_out / velocity) * (sin(theta_out) / sin(angle))))
        ct = abs(2 * sin(angle) * cos(angle) * (1 - phi_func * (v_out / velocity) * (cos(theta_out) / cos(angle))))
        cd = ct * cos(angle) - cn * sin(angle)
        
        return cd, cn, ct
    
    def _sphere_coefficient(self, phi_func: float, velocity: float, accommodation: float,
                          nu: float, wall_temp: float, t_in: float, s: float, hyperthermal: bool) -> float:
        """Calculate Schamberg drag coefficient for sphere."""
        v_out = velocity * sqrt(1 + accommodation * (wall_temp / t_in - 1))
        
        # Definite integral (simplified)
        if nu == 1:
            i1_val = 1 / 4
        elif nu == 500:
            i1_val = 1 / 3
        else:
            i1_val = 1 / 4  # Default approximation
        
        f_of_nu = 2 * (i1_val - (1 / (nu + 3)))
        cd_inf = 2 * (1 + phi_func * (v_out / velocity) * f_of_nu)
        
        if not hyperthermal:
            # Non-hyperthermal correction
            cd = ((2 + sqrt(1 + s**2)) / 3) * sqrt(1 + s**2) * cd_inf
        else:
            cd = cd_inf
        
        return cd


def create_gsi_model(model_type: str) -> GSIModel:
    """
    Factory function to create GSI model instances.
    
    Args:
        model_type: Type of GSI model ('sentman', 'cll', 'schamberg')
        
    Returns:
        GSI model instance
    """
    model_type = model_type.lower().strip()
    
    if model_type == 'sentman':
        return SentmanModel()
    elif model_type == 'cll':
        return CLLModel()
    elif model_type == 'schamberg':
        return SchambergModel()
    else:
        raise GSIModelError(f"Unknown GSI model: {model_type}. "
                          f"Available: sentman, cll, schamberg")