"""
Main drag calculation engine for VECTOR.

This module provides the high-level DragCalculator class that orchestrates
all components to perform satellite drag coefficient calculations.
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from .geometry import Geometry, create_geometry
from .atmosphere import AtmosphericComposition
from .materials import SurfaceMaterial
from .gsi_models import create_gsi_model, GSIModel
from .accommodation import AccommodationCalculator
from .constants import DefaultPhysics
from .exceptions import CalculationError, ValidationError


@dataclass
class DragResult:
    """Result of drag coefficient calculation."""
    drag_coefficient: float          # Overall drag coefficient
    projected_area: float           # Projected area [m²]
    force_coefficient: float        # Force coefficient [m²]
    energy_accommodation: float     # Energy accommodation coefficient
    
    # Optional detailed results
    lift_coefficient: Optional[float] = None
    normal_coefficient: Optional[float] = None
    axial_coefficient: Optional[float] = None
    force_components: Optional[np.ndarray] = None  # [Fx, Fy, Fz]
    torque_components: Optional[np.ndarray] = None  # [Tx, Ty, Tz]


@dataclass
class CalculationParameters:
    """Parameters for drag calculation."""
    # Geometry parameters
    geometry_type: str
    diameter: Optional[float] = None
    length: Optional[float] = None
    area: Optional[float] = None
    geometry_file: Optional[str] = None
    
    # Orientation parameters
    pitch_deg: float = 0.0
    sideslip_deg: float = 0.0
    
    # Environmental parameters
    velocity: float = 7800.0  # m/s
    temperature: float = 1000.0  # K
    
    # Atmospheric composition (particles/m³)
    n_n2: float = 0.0
    n_o2: float = 0.0
    n_o: float = 0.0
    n_he: float = 0.0
    n_h: float = 0.0
    
    # Surface properties
    surface_material: str = "SiO2"
    surface_mass_amu: float = 65.0
    
    # GSI model parameters
    gsi_model: str = "sesam"  # "sesam", "goodman", "fixed", "cll", "laboratory"
    fixed_accommodation: Optional[float] = None
    
    # Advanced parameters
    wall_temperature: float = DefaultPhysics.WALL_TEMPERATURE
    center_of_mass_offset: Optional[np.ndarray] = None


class DragCalculator:
    """
    High-level drag coefficient calculator for satellites.
    
    This class orchestrates all components to calculate drag coefficients
    for different satellite geometries in atmospheric environments.
    """
    
    def __init__(self):
        """Initialize drag calculator."""
        self.accommodation_calc = AccommodationCalculator()
    
    def calculate_drag(self, params: CalculationParameters) -> DragResult:
        """
        Calculate drag coefficient and related properties.
        
        Args:
            params: Calculation parameters
            
        Returns:
            DragResult with calculated values
        """
        # Validate parameters
        self._validate_parameters(params)
        
        # Create components
        geometry = self._create_geometry(params)
        atmosphere = self._create_atmosphere(params)
        material = SurfaceMaterial(params.surface_material)
        
        # Calculate accommodation coefficient
        accommodation = self._calculate_accommodation(params, atmosphere)
        
        # Determine GSI model and calculate coefficients
        coefficients = self._calculate_gsi_coefficients(
            params, geometry, atmosphere, material, accommodation)
        
        # Calculate projected area
        projected_area = geometry.projected_area(params.pitch_deg, params.sideslip_deg)
        
        # Create result
        result = DragResult(
            drag_coefficient=coefficients['CD'],
            projected_area=projected_area,
            force_coefficient=coefficients['CD'] * projected_area,
            energy_accommodation=accommodation,
            lift_coefficient=coefficients.get('CL'),
            normal_coefficient=coefficients.get('CN'),
            axial_coefficient=coefficients.get('CA')
        )
        
        return result
    
    def calculate_multi_point(self, 
                            base_params: CalculationParameters,
                            variable_params: List[Dict[str, float]]) -> List[DragResult]:
        """
        Calculate drag for multiple parameter sets.
        
        Args:
            base_params: Base parameters to use for all calculations
            variable_params: List of parameter dictionaries to vary
            
        Returns:
            List of DragResult objects
        """
        results = []
        
        for var_params in variable_params:
            # Create modified parameters
            params = CalculationParameters(**{
                **base_params.__dict__,
                **var_params
            })
            
            # Calculate drag
            result = self.calculate_drag(params)
            results.append(result)
        
        return results
    
    def _validate_parameters(self, params: CalculationParameters) -> None:
        """Validate calculation parameters."""
        if params.velocity <= 0:
            raise ValidationError("Velocity must be positive", "velocity", params.velocity)
        
        if params.temperature <= 0:
            raise ValidationError("Temperature must be positive", "temperature", params.temperature)
        
        if params.surface_mass_amu < 1:
            raise ValidationError("Surface mass must be >= 1 amu", "surface_mass_amu", params.surface_mass_amu)
        
        # Validate geometry-specific parameters
        if params.geometry_type.lower() == "sphere":
            if not params.diameter or params.diameter <= 0:
                raise ValidationError("Sphere requires positive diameter", "diameter", params.diameter)
        elif params.geometry_type.lower() == "plate":
            if not params.area or params.area <= 0:
                raise ValidationError("Plate requires positive area", "area", params.area)
        elif params.geometry_type.lower() == "cylinder":
            if not params.diameter or params.diameter <= 0:
                raise ValidationError("Cylinder requires positive diameter", "diameter", params.diameter)
            if not params.length or params.length <= 0:
                raise ValidationError("Cylinder requires positive length", "length", params.length)
        elif params.geometry_type.lower() == "custom":
            if not params.geometry_file:
                raise ValidationError("Custom geometry requires geometry file", "geometry_file", params.geometry_file)
        
        # Validate accommodation model
        if params.gsi_model.lower() == "fixed" and params.fixed_accommodation is None:
            raise ValidationError("Fixed GSI model requires fixed_accommodation value", 
                                "fixed_accommodation", params.fixed_accommodation)
    
    def _create_geometry(self, params: CalculationParameters) -> Geometry:
        """Create geometry object from parameters."""
        geometry_type = params.geometry_type.lower()
        
        if geometry_type == "sphere":
            return create_geometry("sphere", diameter=params.diameter)
        elif geometry_type == "plate":
            return create_geometry("plate", area=params.area)
        elif geometry_type == "cylinder":
            return create_geometry("cylinder", diameter=params.diameter, length=params.length)
        elif geometry_type == "custom":
            # For now, create a simple placeholder - full VRML parsing would be implemented here
            raise NotImplementedError("Custom geometry not yet fully implemented in refactored version")
        else:
            raise ValueError(f"Unknown geometry type: {geometry_type}")
    
    def _create_atmosphere(self, params: CalculationParameters) -> AtmosphericComposition:
        """Create atmospheric composition from parameters."""
        return AtmosphericComposition(
            n_n2=params.n_n2,
            n_o2=params.n_o2,
            n_o=params.n_o,
            n_he=params.n_he,
            n_h=params.n_h
        )
    
    def _calculate_accommodation(self, 
                               params: CalculationParameters,
                               atmosphere: AtmosphericComposition) -> float:
        """Calculate energy accommodation coefficient."""
        gsi_model = params.gsi_model.lower()
        
        if gsi_model == "sesam":
            return self.accommodation_calc.calculate_sesam_accommodation(
                atmosphere=atmosphere,
                velocity=params.velocity,
                temperature=params.temperature,
                surface_mass_amu=params.surface_mass_amu
            )
        elif gsi_model == "goodman":
            return self.accommodation_calc.calculate_goodman_accommodation(
                atmosphere=atmosphere,
                surface_mass_amu=params.surface_mass_amu
            )
        elif gsi_model == "fixed":
            return self.accommodation_calc.calculate_fixed_accommodation(
                params.fixed_accommodation
            )
        else:
            # For CLL and laboratory models, use a default value
            # The actual accommodation will be calculated within the GSI model
            return 0.8  # Default value
    
    def _calculate_gsi_coefficients(self,
                                  params: CalculationParameters,
                                  geometry: Geometry,
                                  atmosphere: AtmosphericComposition,
                                  material: SurfaceMaterial,
                                  accommodation: float) -> Dict[str, float]:
        """Calculate GSI model coefficients."""
        gsi_model_name = params.gsi_model.lower()
        
        # Map GSI model names to implementations
        if gsi_model_name in ["sesam", "goodman", "fixed"]:
            # Use Sentman model for these accommodation models
            model = create_gsi_model("sentman")
            shape = self._get_sentman_shape(params.geometry_type)
        elif gsi_model_name == "cll":
            model = create_gsi_model("cll")
            shape = self._get_cll_shape(params.geometry_type)
            # CLL model needs special handling for material properties
            return self._calculate_cll_coefficients(
                model, params, geometry, atmosphere, material, accommodation, shape)
        elif gsi_model_name == "laboratory":
            # Use combined CLL + Sentman model based on material properties
            return self._calculate_laboratory_coefficients(
                params, geometry, atmosphere, material, accommodation)
        else:
            raise CalculationError(f"Unknown GSI model: {gsi_model_name}")
        
        # Calculate coefficients for each gas species and combine
        return self._calculate_multi_species_coefficients(
            model, params, atmosphere, accommodation, shape)
    
    def _get_sentman_shape(self, geometry_type: str) -> str:
        """Map geometry type to Sentman model shape."""
        mapping = {
            "sphere": "sphere",
            "plate": "surface",  # Use surface instead of surfacespec for plates
            "cylinder": "cylinder",
            "custom": "surface"  # Treat custom as surface
        }
        return mapping.get(geometry_type.lower(), "surface")
    
    def _get_cll_shape(self, geometry_type: str) -> str:
        """Map geometry type to CLL model shape."""
        mapping = {
            "sphere": "sphere",
            "plate": "plate",
            "cylinder": "plate",  # CLL doesn't have cylinder, use plate
            "custom": "plate"
        }
        return mapping.get(geometry_type.lower(), "plate")
    
    def _calculate_cll_coefficients(self,
                                   model: GSIModel,
                                   params: CalculationParameters,
                                   geometry: Geometry,
                                   atmosphere: AtmosphericComposition,
                                   material: SurfaceMaterial,
                                   accommodation: float,
                                   shape: str) -> Dict[str, float]:
        """Calculate CLL coefficients with material properties."""
        species_names = ['N2', 'O2', 'O', 'He', 'H']
        densities = atmosphere.number_densities
        masses = atmosphere.masses
        
        # Initialize coefficient arrays
        cd_parts = np.zeros(5)
        cl_parts = np.zeros(5)
        cn_parts = np.zeros(5)
        ca_parts = np.zeros(5)
        
        # Calculate for each species
        for i, species in enumerate(species_names):
            if densities[i] == 0:
                continue
            
            # Calculate incident angle for plate geometries
            angle = 0.0
            if shape in ["surfacespec", "plate"] and params.geometry_type.lower() == "plate":
                angle = np.radians(90 - params.pitch_deg)  # Convert to incident angle
            
            # Get material properties - convert angle back to degrees for material methods
            angle_deg = np.degrees(angle)
            alpha_n = material.get_normal_accommodation(angle_deg)
            sigma_t = material.get_tangential_accommodation(angle_deg)
            
            # Calculate coefficients for this species with CLL-specific parameters
            coeffs = model.calculate_coefficients(
                angle=angle,
                velocity=params.velocity,
                gas_temperature=params.temperature,
                wall_temperature=params.wall_temperature,
                gas_mass=masses[i],
                accommodation=accommodation,  # Not used by CLL but required for interface
                alpha_n=alpha_n,
                sigma_t=sigma_t,
                shape=shape
            )
            
            cd_parts[i] = coeffs['CD']
            cl_parts[i] = coeffs['CL']
            cn_parts[i] = coeffs['CN']
            ca_parts[i] = coeffs['CA']
        
        # Weight by number density
        weights = densities / np.sum(densities)
        
        return {
            'CD': np.sum(weights * cd_parts),
            'CL': np.sum(weights * cl_parts),
            'CN': np.sum(weights * cn_parts),
            'CA': np.sum(weights * ca_parts)
        }
    
    def _calculate_multi_species_coefficients(self,
                                            model: GSIModel,
                                            params: CalculationParameters,
                                            atmosphere: AtmosphericComposition,
                                            accommodation: float,
                                            shape: str) -> Dict[str, float]:
        """Calculate coefficients for multiple gas species and combine."""
        species_names = ['N2', 'O2', 'O', 'He', 'H']
        densities = atmosphere.number_densities
        masses = atmosphere.masses
        
        # Initialize coefficient arrays
        cd_parts = np.zeros(5)
        cl_parts = np.zeros(5)
        cn_parts = np.zeros(5)
        ca_parts = np.zeros(5)
        
        # Calculate for each species
        for i, species in enumerate(species_names):
            if densities[i] == 0:
                continue
            
            # Calculate incident angle for plate geometries
            angle = 0.0
            if shape in ["surfacespec", "plate"] and params.geometry_type.lower() == "plate":
                angle = np.radians(90 - params.pitch_deg)  # Convert to incident angle
            
            # Calculate coefficients for this species
            coeffs = model.calculate_coefficients(
                angle=angle,
                velocity=params.velocity,
                gas_temperature=params.temperature,
                wall_temperature=params.wall_temperature,
                gas_mass=masses[i],
                accommodation=accommodation,
                shape=shape
            )
            
            cd_parts[i] = coeffs['CD']
            cl_parts[i] = coeffs['CL']
            cn_parts[i] = coeffs['CN']
            ca_parts[i] = coeffs['CA']
        
        # Combine species using mass-weighted average
        mass_densities = masses * densities
        total_mass_density = np.sum(mass_densities)
        
        if total_mass_density == 0:
            raise CalculationError("Zero total atmospheric density")
        
        combined_coeffs = {
            'CD': np.dot(cd_parts, mass_densities) / total_mass_density,
            'CL': np.dot(cl_parts, mass_densities) / total_mass_density,
            'CN': np.dot(cn_parts, mass_densities) / total_mass_density,
            'CA': np.dot(ca_parts, mass_densities) / total_mass_density
        }
        
        return combined_coeffs
    
    def _calculate_laboratory_coefficients(self,
                                         params: CalculationParameters,
                                         geometry: Geometry,
                                         atmosphere: AtmosphericComposition,
                                         material: SurfaceMaterial,
                                         base_accommodation: float) -> Dict[str, float]:
        """Calculate coefficients using laboratory-derived parameters."""
        # Get material properties based on incident angle
        incident_angle_deg = 180 - params.pitch_deg  # Convert to material convention
        
        if params.geometry_type.lower() == "sphere":
            # Use surface-averaged properties for sphere
            from .geometry import SphereGeometry
            if isinstance(geometry, SphereGeometry):
                props = material.get_sphere_averaged_properties(geometry.radius)
            else:
                props = material.get_all_properties(incident_angle_deg)
        else:
            props = material.get_all_properties(incident_angle_deg)
        
        # Create CLL model for quasi-specular component
        cll_model = create_gsi_model("cll")
        cll_shape = self._get_cll_shape(params.geometry_type)
        
        # Create Sentman model for cosine component
        sentman_model = create_gsi_model("sentman")
        sentman_shape = self._get_sentman_shape(params.geometry_type)
        
        # Calculate coefficients for both models
        cll_coeffs = self._calculate_multi_species_coefficients(
            cll_model, params, atmosphere, props['accommodation'], cll_shape)
        
        sentman_coeffs = self._calculate_multi_species_coefficients(
            sentman_model, params, atmosphere, props['accommodation'], sentman_shape)
        
        # Combine using cosine fraction weighting
        cos_frac = props['cos_frac']
        combined_coeffs = {
            'CD': (1 - cos_frac) * cll_coeffs['CD'] + cos_frac * sentman_coeffs['CD'],
            'CL': (1 - cos_frac) * cll_coeffs['CL'] + cos_frac * sentman_coeffs['CL'],
            'CN': (1 - cos_frac) * cll_coeffs['CN'] + cos_frac * sentman_coeffs['CN'],
            'CA': (1 - cos_frac) * cll_coeffs['CA'] + cos_frac * sentman_coeffs['CA']
        }
        
        return combined_coeffs


# Convenience functions for backward compatibility and simple usage
def calculate_sphere_drag(diameter: float,
                         velocity: float,
                         temperature: float,
                         atmosphere_dict: Dict[str, float],
                         surface_material: str = "SiO2",
                         gsi_model: str = "sesam") -> DragResult:
    """
    Convenience function to calculate drag for a sphere.
    
    Args:
        diameter: Sphere diameter [m]
        velocity: Velocity magnitude [m/s]
        temperature: Atmospheric temperature [K]
        atmosphere_dict: Atmospheric composition {'O': n_o, 'O2': n_o2, ...}
        surface_material: Surface material name
        gsi_model: GSI model name
        
    Returns:
        DragResult
    """
    params = CalculationParameters(
        geometry_type="sphere",
        diameter=diameter,
        velocity=velocity,
        temperature=temperature,
        surface_material=surface_material,
        gsi_model=gsi_model,
        **{f"n_{species.lower()}": density for species, density in atmosphere_dict.items()}
    )
    
    calculator = DragCalculator()
    return calculator.calculate_drag(params)


def calculate_plate_drag(area: float,
                        pitch_deg: float,
                        velocity: float,
                        temperature: float,
                        atmosphere_dict: Dict[str, float],
                        surface_material: str = "SiO2",
                        gsi_model: str = "sesam") -> DragResult:
    """
    Convenience function to calculate drag for a flat plate.
    
    Args:
        area: Plate area [m²]
        pitch_deg: Pitch angle [degrees]
        velocity: Velocity magnitude [m/s]
        temperature: Atmospheric temperature [K]
        atmosphere_dict: Atmospheric composition {'O': n_o, 'O2': n_o2, ...}
        surface_material: Surface material name
        gsi_model: GSI model name
        
    Returns:
        DragResult
    """
    params = CalculationParameters(
        geometry_type="plate",
        area=area,
        pitch_deg=pitch_deg,
        velocity=velocity,
        temperature=temperature,
        surface_material=surface_material,
        gsi_model=gsi_model,
        **{f"n_{species.lower()}": density for species, density in atmosphere_dict.items()}
    )
    
    calculator = DragCalculator()
    return calculator.calculate_drag(params)