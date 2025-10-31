# VECTOR Python Package Documentation

## Overview

VECTOR (Visually Enhanced Coefficient Tool for Orbital Recovery) is a Python package for calculating satellite atmospheric drag coefficients. This refactored version provides a modern, Pythonic API while maintaining backward compatibility with the original MATLAB-derived interface.

## Key Features

- **Multiple Satellite Geometries**: Spheres, plates, cylinders, and custom geometries
- **Various GSI Models**: Sentman, CLL, Schamberg, SESAM, Goodman, and laboratory-derived models
- **Material Properties**: Built-in properties for SiO2, aluminum, Teflon, and FR4
- **Multi-species Atmospheres**: Support for N₂, O₂, O, He, and H
- **Type Safety**: Full type hints throughout the codebase
- **Comprehensive Documentation**: Detailed docstrings and examples
- **Error Handling**: Proper validation and helpful error messages
- **Backward Compatibility**: Original MAIN function interface preserved

## Installation

```bash
pip install vector-python
```

## Quick Start

### Modern API

```python
from vector_python import DragCalculator, CalculationParameters

# Set up calculation parameters
params = CalculationParameters(
    geometry_type="sphere",
    diameter=1.2,              # meters
    velocity=7800.0,           # m/s
    temperature=1200.0,        # K
    n_o=1e11,                 # atomic oxygen [particles/m³]
    n_o2=1e6,                 # molecular oxygen [particles/m³]
    surface_material="SiO2",
    gsi_model="sesam"
)

# Calculate drag
calculator = DragCalculator()
result = calculator.calculate_drag(params)

print(f"Drag coefficient: {result.drag_coefficient:.4f}")
print(f"Projected area: {result.projected_area:.4f} m²")
print(f"Energy accommodation: {result.energy_accommodation:.4f}")
```

### Convenience Functions

```python
from vector_python import calculate_sphere_drag

atmosphere = {
    'O': 1e11,   # atomic oxygen
    'O2': 1e6,   # molecular oxygen  
    'N2': 1e6    # molecular nitrogen
}

result = calculate_sphere_drag(
    diameter=1.2,
    velocity=7800.0,
    temperature=1200.0,
    atmosphere_dict=atmosphere,
    surface_material="SiO2",
    gsi_model="sesam"
)
```

### Legacy Compatibility

```python
from vector_python import MAIN, GeometryType, GSIModelType
import numpy as np

CD_status, CD, Aout, Fcoef, alpha_out = MAIN(
    obj_type=GeometryType.SPHERE,
    D=1.2,                          # diameter [m]
    L=0.0, A=0.0,                   # not used for sphere
    Phi=0.0, Theta=0.0,             # angles [deg]
    Ta=1200.0, Va=7800.0,           # temperature [K], velocity [m/s]
    n_O=1e11, n_O2=1e6, n_N2=1e6, n_He=1e6, n_H=1e4,  # densities
    GSI_model=GSIModelType.SESAM,   # GSI model
    alpha=0.8,                      # accommodation (not used for SESAM)
    m_s=65.0,                       # surface mass [amu]
    POSVEL=np.array([]).T,          # empty for single point
    fnamesurf=""                    # not used for sphere
)
```

## API Reference

### Core Classes

#### `DragCalculator`
Main class for performing drag calculations.

**Methods:**
- `calculate_drag(params: CalculationParameters) -> DragResult`
- `calculate_multi_point(base_params, variable_params) -> List[DragResult]`

#### `CalculationParameters`
Dataclass containing all calculation parameters.

**Key Parameters:**
- `geometry_type: str` - "sphere", "plate", "cylinder", "custom"
- `diameter: float` - Diameter for spheres/cylinders [m]  
- `area: float` - Area for plates [m²]
- `length: float` - Length for cylinders [m]
- `pitch_deg: float` - Pitch angle [degrees]
- `sideslip_deg: float` - Sideslip angle [degrees]
- `velocity: float` - Velocity magnitude [m/s]
- `temperature: float` - Atmospheric temperature [K]
- `n_n2, n_o2, n_o, n_he, n_h: float` - Species densities [particles/m³]
- `surface_material: str` - "SiO2", "aluminum", "Teflon", "FR4"
- `gsi_model: str` - "sesam", "goodman", "fixed", "cll", "laboratory"

#### `DragResult`
Result dataclass containing calculated values.

**Attributes:**
- `drag_coefficient: float` - Overall drag coefficient
- `projected_area: float` - Projected area [m²]
- `force_coefficient: float` - Force coefficient [m²]
- `energy_accommodation: float` - Energy accommodation coefficient
- Optional: `lift_coefficient`, `normal_coefficient`, `axial_coefficient`

### Geometry Classes

#### `SphereGeometry(diameter: float)`
Spherical satellite geometry.

#### `PlateGeometry(area: float)`
Flat plate satellite geometry.

#### `CylinderGeometry(diameter: float, length: float)`
Cylindrical satellite geometry.

#### `CustomGeometry(mesh: TriangleMesh)`
Custom geometry from triangular mesh.

### Atmospheric Composition

#### `AtmosphericComposition`
Handles atmospheric gas species and properties.

```python
atmosphere = AtmosphericComposition(
    n_n2=1e6,   # N₂ density [particles/m³]
    n_o2=1e6,   # O₂ density
    n_o=1e11,   # O density  
    n_he=1e6,   # He density
    n_h=1e4     # H density
)

# Properties
print(atmosphere.total_number_density)
print(atmosphere.mean_molecular_mass)
print(atmosphere.get_active_species())
```

### Surface Materials

#### `SurfaceMaterial(material_name: str)`
Surface material properties for gas-surface interactions.

```python
material = SurfaceMaterial("SiO2")

# Get properties at specific incident angle
props = material.get_all_properties(45.0)  # degrees
print(props['accommodation'])
print(props['alpha_n'])
print(props['sigma_t'])

# Get sphere-averaged properties
sphere_props = material.get_sphere_averaged_properties(radius=0.6)
```

### GSI Models

Gas-Surface Interaction models are available through the factory function:

```python
from vector_python import create_gsi_model

sentman_model = create_gsi_model("sentman")
cll_model = create_gsi_model("cll") 
schamberg_model = create_gsi_model("schamberg")
```

## GSI Model Details

### SESAM Model
Surface Energy and Species Accommodation Model. Calculates accommodation based on atomic oxygen interactions and surface chemistry.

### Goodman Model  
Simple mass-ratio based accommodation coefficient:
```
α = 3.6 * μ / (1 + μ)²
```
where μ = gas_mass / surface_mass

### Fixed Model
Uses a constant accommodation coefficient value.

### CLL Model
Cercignani-Lampis-Lord model with separate normal and tangential accommodation coefficients.

### Laboratory Model
Uses laboratory-derived parameters interpolated by incident angle, with combined cosine and quasi-specular reflection components.

## Material Properties

Built-in materials with incident-angle-dependent properties:

- **SiO2**: Silicon dioxide (glass)
- **aluminum**: Aluminum metal  
- **Teflon**: PTFE polymer
- **FR4**: Fiberglass PCB material

Each material includes:
- Normal accommodation coefficient (α_n)
- Tangential momentum accommodation (σ_t)  
- Cosine reflection fraction
- Energy accommodation coefficient

## Multi-Point Calculations

Calculate drag for parameter sweeps:

```python
base_params = CalculationParameters(
    geometry_type="sphere",
    diameter=1.0,
    # ... other fixed parameters
)

# Vary velocity
variable_params = [
    {'velocity': 6000},
    {'velocity': 7000}, 
    {'velocity': 8000}
]

results = calculator.calculate_multi_point(base_params, variable_params)
```

## Error Handling

The package provides specific exception types:

- `ValidationError`: Invalid parameter values
- `GeometryError`: Geometry-related issues
- `MaterialError`: Material property problems
- `AtmosphereError`: Atmospheric composition issues
- `CalculationError`: Calculation failures
- `GSIModelError`: GSI model problems
- `FileFormatError`: File parsing errors

## Performance Considerations

- **Caching**: Material properties are cached for repeated calculations
- **Vectorization**: Numpy is used extensively for efficient calculations
- **Memory**: Large geometry meshes may require significant memory

## Validation and Testing

The package includes comprehensive validation:

- Parameter range checking
- Physical consistency validation
- Unit testing (run with `pytest`)
- Comparison with original MATLAB results

## Migration from Legacy Code

### Original MATLAB/Python Interface

```python
# Old way
CD_status, CD, Aout, Fcoef, alpha_out = MAIN(
    1, 1.2, 0.0, 0.0, 0.0, 0.0, 1200.0, 7800.0,
    1e11, 1e6, 1e6, 1e6, 1e4, -1, 0.8, 65.0,
    np.array([]).T, ""
)
drag_coeff = CD[0, 0]
```

### New Pythonic Interface

```python
# New way
params = CalculationParameters(
    geometry_type="sphere",
    diameter=1.2,
    temperature=1200.0,
    velocity=7800.0,
    n_o=1e11, n_o2=1e6, n_n2=1e6, n_he=1e6, n_h=1e4,
    gsi_model="sesam",
    surface_mass_amu=65.0
)

result = DragCalculator().calculate_drag(params)
drag_coeff = result.drag_coefficient
```

## Examples

See `examples.py` for comprehensive usage examples including:

- Basic drag calculations
- Material comparisons  
- Multi-point parameter sweeps
- Error handling
- Legacy compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## References

1. Sentman, L. H. (1961). Free molecule flow theory and its application to the determination of aerodynamic forces.
2. Cercignani, C., & Lampis, M. (1971). Kinetic models for gas-surface interactions.
3. Pilinski, M. D., et al. (2010). Semi-empirical satellite accommodation model for spherical and plate-like satellites.

## Support

For questions, issues, or feature requests, please use the GitHub issue tracker.