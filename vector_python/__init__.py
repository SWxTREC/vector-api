"""
VECTOR: Visually Enhanced Coefficient Tool for Orbital Recovery

A Python package for calculating satellite atmospheric drag coefficients using
various gas-surface interaction models and satellite geometries.

This package provides both a modern, Pythonic API and backward compatibility
with the original MATLAB-derived interface.
"""

# Version information
__version__ = "1.0.0"
__author__ = "Marcin Pilinski, Greg Lucas"

# Main API exports
from .drag_calculator import (
    DragCalculator,
    DragResult,
    CalculationParameters,
    calculate_sphere_drag,
    calculate_plate_drag
)

from .geometry import (
    Geometry,
    SphereGeometry,
    PlateGeometry, 
    CylinderGeometry,
    CustomGeometry,
    create_geometry
)

from .atmosphere import (
    AtmosphericComposition,
    GasSpeciesData
)

from .materials import (
    SurfaceMaterial,
    MaterialProperties
)

from .gsi_models import (
    GSIModel,
    SentmanModel,
    CLLModel,
    SchambergModel,
    create_gsi_model
)

from .accommodation import (
    AccommodationCalculator,
    langmuir_k_model
)

# Legacy API for backward compatibility
from .legacy import (
    MAIN,
    calculate_sphere_drag_legacy,
    calculate_plate_drag_legacy
)

# Constants and utilities
from .constants import (
    AtomicMasses,
    GasSpecies,
    GeometryType,
    GSIModel as GSIModelType,
    CLLDefaults,
    MATERIAL_PROPERTIES
)

from .exceptions import (
    VectorError,
    ValidationError,
    GeometryError,
    MaterialError,
    AtmosphereError,
    CalculationError,
    GSIModelError,
    FileFormatError
)

# Public API
__all__ = [
    # Main classes
    'DragCalculator',
    'DragResult', 
    'CalculationParameters',
    
    # Geometry classes
    'Geometry',
    'SphereGeometry',
    'PlateGeometry',
    'CylinderGeometry', 
    'CustomGeometry',
    'create_geometry',
    
    # Atmosphere and materials
    'AtmosphericComposition',
    'GasSpeciesData',
    'SurfaceMaterial',
    'MaterialProperties',
    
    # GSI models
    'GSIModel',
    'SentmanModel', 
    'CLLModel',
    'SchambergModel',
    'create_gsi_model',
    
    # Accommodation
    'AccommodationCalculator',
    'langmuir_k_model',
    
    # Convenience functions
    'calculate_sphere_drag',
    'calculate_plate_drag',
    
    # Legacy compatibility
    'MAIN',
    'calculate_sphere_drag_legacy',
    'calculate_plate_drag_legacy',
    
    # Constants
    'AtomicMasses',
    'GasSpecies',
    'GeometryType',
    'GSIModelType',
    'CLLDefaults',
    'MATERIAL_PROPERTIES',
    
    # Exceptions
    'VectorError',
    'ValidationError',
    'GeometryError',
    'MaterialError',
    'AtmosphereError',
    'CalculationError',
    'GSIModelError',
    'FileFormatError'
]