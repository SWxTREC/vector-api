"""
Surface material properties module for VECTOR drag calculations.

This module provides classes to handle different surface materials and their
gas-surface interaction properties.
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass

from .constants import MATERIAL_PROPERTIES
from .exceptions import MaterialError
from .utils import interpolate_material_property


@dataclass
class MaterialProperties:
    """Data class for material properties at different incident angles."""
    incident_angles: List[float]  # degrees
    alpha_n: List[float]         # Normal accommodation coefficients
    sigma_t: List[float]         # Tangential momentum accommodation
    cos_frac: List[float]        # Cosine fraction
    accommodation: List[float]   # Energy accommodation coefficients


class SurfaceMaterial:
    """
    Represents surface material properties for gas-surface interactions.
    
    This class encapsulates material-specific properties and provides methods
    to calculate accommodation coefficients and other GSI parameters based on
    incident angles and other conditions.
    """
    
    def __init__(self, material_name: str):
        """
        Initialize surface material.
        
        Args:
            material_name: Name of the material ('SiO2', 'aluminum', 'Teflon', 'FR4')
        """
        self.name = material_name.strip()
        
        if self.name not in MATERIAL_PROPERTIES:
            available = list(MATERIAL_PROPERTIES.keys())
            raise MaterialError(f"Unknown material: {self.name}. "
                              f"Available materials: {available}")
        
        # Load material properties
        props_dict = MATERIAL_PROPERTIES[self.name]
        self._properties = MaterialProperties(**props_dict)
    
    @property
    def available_materials(self) -> List[str]:
        """Get list of available material names."""
        return list(MATERIAL_PROPERTIES.keys())
    
    def get_normal_accommodation(self, incident_angle_deg: float) -> float:
        """
        Get normal accommodation coefficient at given incident angle.
        
        Args:
            incident_angle_deg: Incident angle in degrees
            
        Returns:
            Normal accommodation coefficient (0-1)
        """
        return interpolate_material_property(
            incident_angle_deg,
            self._properties.incident_angles,
            self._properties.alpha_n,
            bounds=(0.0, 1.0)
        )
    
    def get_tangential_accommodation(self, incident_angle_deg: float) -> float:
        """
        Get tangential momentum accommodation coefficient at given incident angle.
        
        Args:
            incident_angle_deg: Incident angle in degrees
            
        Returns:
            Tangential momentum accommodation coefficient (0-1)
        """
        return interpolate_material_property(
            incident_angle_deg,
            self._properties.incident_angles,
            self._properties.sigma_t,
            bounds=(0.0, 1.0)
        )
    
    def get_cosine_fraction(self, incident_angle_deg: float) -> float:
        """
        Get cosine reflection fraction at given incident angle.
        
        Args:
            incident_angle_deg: Incident angle in degrees
            
        Returns:
            Cosine fraction (0-1)
        """
        return interpolate_material_property(
            incident_angle_deg,
            self._properties.incident_angles,
            self._properties.cos_frac,
            bounds=(0.0, 1.0)
        )
    
    def get_energy_accommodation(self, incident_angle_deg: float) -> float:
        """
        Get energy accommodation coefficient at given incident angle.
        
        Args:
            incident_angle_deg: Incident angle in degrees
            
        Returns:
            Energy accommodation coefficient (0-1)
        """
        return interpolate_material_property(
            incident_angle_deg,
            self._properties.incident_angles,
            self._properties.accommodation,
            bounds=(0.0, 1.0)
        )
    
    def get_all_properties(self, incident_angle_deg: float) -> Dict[str, float]:
        """
        Get all material properties at a given incident angle.
        
        Args:
            incident_angle_deg: Incident angle in degrees
            
        Returns:
            Dictionary with all properties
        """
        return {
            'alpha_n': self.get_normal_accommodation(incident_angle_deg),
            'sigma_t': self.get_tangential_accommodation(incident_angle_deg),
            'cos_frac': self.get_cosine_fraction(incident_angle_deg),
            'accommodation': self.get_energy_accommodation(incident_angle_deg)
        }
    
    def get_sphere_averaged_properties(self, radius: float) -> Dict[str, float]:
        """
        Get surface-area-weighted average properties for a sphere.
        
        For spheres, properties are weighted by the surface area of each
        angular segment to get effective average values.
        
        Args:
            radius: Sphere radius in meters
            
        Returns:
            Dictionary with averaged properties
        """
        # Angular resolution for integration
        inc_angle_res = 2.5  # degrees
        num_sections = int(90 / inc_angle_res) + 1
        
        # Initialize weighted sums
        cos_frac_sum = 0.0
        accommodation_sum = 0.0
        alpha_n_sum = 0.0
        sigma_t_sum = 0.0
        total_area = 0.0
        
        for i in range(num_sections - 1):  # Exclude back hemisphere
            # Calculate mid-angle for this section
            angle_bound1 = i * inc_angle_res
            angle_bound2 = (i + 1) * inc_angle_res
            mid_angle = (angle_bound1 + angle_bound2) / 2
            
            # Calculate surface area for this angular segment
            h1 = radius * np.cos(np.radians(angle_bound1))
            h2 = radius * np.cos(np.radians(angle_bound2))
            
            segment_area = 2 * np.pi * radius * (h1 - h2)
            
            # Get properties at mid-angle
            props = self.get_all_properties(mid_angle)
            
            # Add to weighted sums
            cos_frac_sum += segment_area * props['cos_frac']
            accommodation_sum += segment_area * props['accommodation']
            alpha_n_sum += segment_area * props['alpha_n']
            sigma_t_sum += segment_area * props['sigma_t']
            total_area += segment_area
        
        # Calculate weighted averages
        if total_area == 0:
            raise MaterialError("Zero total surface area in sphere averaging")
        
        return {
            'cos_frac': cos_frac_sum / total_area,
            'accommodation': accommodation_sum / total_area,
            'alpha_n': alpha_n_sum / total_area,
            'sigma_t': sigma_t_sum / total_area
        }
    
    def __repr__(self) -> str:
        """String representation of surface material."""
        return f"SurfaceMaterial('{self.name}')"