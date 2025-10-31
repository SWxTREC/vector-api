"""
Atmospheric composition module for VECTOR drag calculations.

This module provides classes to handle atmospheric composition, gas properties,
and related calculations in a clean, Pythonic way.
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass

from .constants import AtomicMasses, BOLTZMANN_CONSTANT
from .exceptions import AtmosphereError, ValidationError


@dataclass
class GasSpeciesData:
    """Data class for individual gas species properties."""
    name: str
    mass: float  # kg
    number_density: float  # particles/m³
    
    def __post_init__(self):
        """Validate gas species data after initialization."""
        if self.mass <= 0:
            raise ValidationError("Mass must be positive", "mass", self.mass)
        if self.number_density < 0:
            raise ValidationError("Number density must be non-negative", 
                                "number_density", self.number_density)


class AtmosphericComposition:
    """
    Represents the composition of atmospheric gases for drag calculations.
    
    This class handles the composition of different atmospheric gas species,
    their number densities, masses, and provides methods for calculating
    bulk atmospheric properties.
    """
    
    def __init__(self, 
                 n_n2: float = 0.0,
                 n_o2: float = 0.0, 
                 n_o: float = 0.0,
                 n_he: float = 0.0,
                 n_h: float = 0.0):
        """
        Initialize atmospheric composition.
        
        Args:
            n_n2: Number density of N₂ [particles/m³]
            n_o2: Number density of O₂ [particles/m³]
            n_o: Number density of atomic O [particles/m³]
            n_he: Number density of He [particles/m³]
            n_h: Number density of atomic H [particles/m³]
        """
        self._validate_densities(n_n2, n_o2, n_o, n_he, n_h)
        
        self._species = {
            'N2': GasSpeciesData('N2', AtomicMasses.NITROGEN_MOLECULE, n_n2),
            'O2': GasSpeciesData('O2', AtomicMasses.OXYGEN_MOLECULE, n_o2),
            'O': GasSpeciesData('O', AtomicMasses.OXYGEN, n_o),
            'He': GasSpeciesData('He', AtomicMasses.HELIUM, n_he),
            'H': GasSpeciesData('H', AtomicMasses.HYDROGEN, n_h)
        }
    
    @classmethod
    def from_dict(cls, composition: Dict[str, float]) -> 'AtmosphericComposition':
        """
        Create atmospheric composition from dictionary.
        
        Args:
            composition: Dictionary with gas species and their number densities
                        Keys can be 'N2', 'O2', 'O', 'He', 'H' (case insensitive)
        
        Returns:
            AtmosphericComposition instance
        """
        # Normalize keys to uppercase
        normalized = {k.upper(): v for k, v in composition.items()}
        
        return cls(
            n_n2=normalized.get('N2', 0.0),
            n_o2=normalized.get('O2', 0.0),
            n_o=normalized.get('O', 0.0),
            n_he=normalized.get('HE', 0.0),
            n_h=normalized.get('H', 0.0)
        )
    
    def _validate_densities(self, *densities: float) -> None:
        """Validate that all number densities are non-negative."""
        for i, density in enumerate(densities):
            if density < 0:
                species_names = ['N2', 'O2', 'O', 'He', 'H']
                raise ValidationError(
                    "Number density must be non-negative",
                    f"n_{species_names[i]}", density
                )
    
    @property
    def number_densities(self) -> np.ndarray:
        """Get number densities as array in standard order [N2, O2, O, He, H]."""
        return np.array([
            self._species['N2'].number_density,
            self._species['O2'].number_density,
            self._species['O'].number_density,
            self._species['He'].number_density,
            self._species['H'].number_density
        ])
    
    @property
    def masses(self) -> np.ndarray:
        """Get masses as array in standard order [N2, O2, O, He, H]."""
        return np.array([
            self._species['N2'].mass,
            self._species['O2'].mass,
            self._species['O'].mass,
            self._species['He'].mass,
            self._species['H'].mass
        ])
    
    @property 
    def mass_densities(self) -> np.ndarray:
        """Get mass densities (mass * number_density) for each species."""
        return self.masses * self.number_densities
    
    @property
    def total_number_density(self) -> float:
        """Get total number density of all species."""
        return np.sum(self.number_densities)
    
    @property
    def total_mass_density(self) -> float:
        """Get total mass density of all species."""
        return np.sum(self.mass_densities)
    
    @property
    def mean_molecular_mass(self) -> float:
        """
        Calculate the mean molecular mass of the atmospheric mixture.
        
        Returns:
            Mean molecular mass in kg
        """
        if self.total_number_density == 0:
            raise AtmosphereError("Cannot calculate mean molecular mass with zero total density")
        
        return self.total_mass_density / self.total_number_density
    
    @property
    def atomic_oxygen_density(self) -> float:
        """Get atomic oxygen mass density (used for accommodation calculations)."""
        return AtomicMasses.OXYGEN * self._species['O'].number_density
    
    def get_species_data(self, species: str) -> GasSpeciesData:
        """
        Get data for a specific gas species.
        
        Args:
            species: Species name ('N2', 'O2', 'O', 'He', 'H')
            
        Returns:
            GasSpeciesData for the species
        """
        species_upper = species.upper()
        if species_upper not in self._species:
            raise ValueError(f"Unknown species: {species}. "
                           f"Available: {list(self._species.keys())}")
        
        return self._species[species_upper]
    
    def thermal_speed(self, species: str, temperature: float) -> float:
        """
        Calculate thermal speed for a specific gas species.
        
        Args:
            species: Gas species name
            temperature: Temperature in Kelvin
            
        Returns:
            RMS thermal speed in m/s
        """
        if temperature <= 0:
            raise ValidationError("Temperature must be positive", "temperature", temperature)
        
        species_data = self.get_species_data(species)
        return np.sqrt(3 * BOLTZMANN_CONSTANT * temperature / species_data.mass)
    
    def has_species(self, species: str) -> bool:
        """Check if composition has non-zero density for a species."""
        try:
            species_data = self.get_species_data(species)
            return species_data.number_density > 0
        except ValueError:
            return False
    
    def get_active_species(self) -> List[str]:
        """Get list of species with non-zero densities."""
        return [name for name, data in self._species.items() 
                if data.number_density > 0]
    
    def __repr__(self) -> str:
        """String representation of atmospheric composition."""
        active_species = self.get_active_species()
        if not active_species:
            return "AtmosphericComposition(empty)"
        
        species_str = ", ".join([f"{species}: {self._species[species].number_density:.2e}" 
                               for species in active_species])
        return f"AtmosphericComposition({species_str})"