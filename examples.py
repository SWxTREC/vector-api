"""
VECTOR Examples: Demonstration of the refactored drag calculation API

This script demonstrates how to use the new Pythonic API for calculating
satellite drag coefficients, as well as the backward compatibility layer.
"""

import numpy as np
from vector_python import (
    DragCalculator,
    CalculationParameters,
    SurfaceMaterial,
    calculate_sphere_drag,
    calculate_plate_drag,
    MAIN,  # Legacy function
    GeometryType,
    GSIModelType
)


def example_modern_api():
    """Demonstrate the modern, Pythonic API."""
    print("=== Modern API Examples ===\n")
    
    # Example 1: Simple sphere drag calculation
    print("1. Simple Sphere Drag Calculation")
    print("-" * 40)
    
    # Create atmospheric composition (example of using the class directly)
    # atmosphere = AtmosphericComposition(n_o=1e11, n_o2=1e6, n_n2=1e6, n_he=1e6, n_h=1e4)
    
    # Set up calculation parameters
    params = CalculationParameters(
        geometry_type="sphere",
        diameter=1.2,              # meters
        velocity=7800.0,           # m/s
        temperature=1200.0,        # K
        n_o=1e11,
        n_o2=1e6,
        n_n2=1e6,
        n_he=1e6,
        n_h=1e4,
        surface_material="SiO2",
        surface_mass_amu=65.0,
        gsi_model="sesam"
    )
    
    # Calculate drag
    calculator = DragCalculator()
    result = calculator.calculate_drag(params)
    
    print(f"  Drag coefficient: {result.drag_coefficient:.4f}")
    print(f"  Projected area: {result.projected_area:.4f} m²")
    print(f"  Force coefficient: {result.force_coefficient:.4f} m²")
    print(f"  Energy accommodation: {result.energy_accommodation:.4f}")
    print()
    
    # Example 2: Plate with different GSI models
    print("2. Plate with Different GSI Models")
    print("-" * 40)
    
    models = ["sesam", "goodman", "cll", "laboratory"]
    
    for model in models:
        params = CalculationParameters(
            geometry_type="plate",
            area=1.2,                  # m²
            pitch_deg=30.0,            # degrees
            velocity=7750.0,           # m/s
            temperature=800.0,         # K
            n_o=1e11,
            n_o2=1e6,
            n_n2=1e6,
            surface_material="aluminum",
            gsi_model=model
        )
        
        try:
            result = calculator.calculate_drag(params)
            print(f"  {model.upper():12}: CD = {result.drag_coefficient:.4f}, "
                  f"α = {result.energy_accommodation:.4f}")
        except Exception as e:
            print(f"  {model.upper():12}: Error - {e}")
    
    print()
    
    # Example 3: Material comparison
    print("3. Material Property Comparison")
    print("-" * 40)
    
    materials = ["SiO2", "aluminum", "Teflon", "FR4"]
    
    for material in materials:
        # Create surface material
        surf_material = SurfaceMaterial(material)
        
        # Get properties at 45° incident angle
        props = surf_material.get_all_properties(45.0)
        
        print(f"  {material:10}: α_n={props['alpha_n']:.3f}, "
              f"σ_t={props['sigma_t']:.3f}, "
              f"accommodation={props['accommodation']:.3f}")
    
    print()


def example_convenience_functions():
    """Demonstrate convenience functions."""
    print("=== Convenience Functions ===\n")
    
    # Sphere drag calculation
    print("Sphere Drag (convenience function):")
    print("-" * 35)
    
    atmosphere_dict = {
        'O': 1e11,
        'O2': 1e6,
        'N2': 1e6,
        'He': 1e6,
        'H': 1e4
    }
    
    result = calculate_sphere_drag(
        diameter=1.2,
        velocity=7800.0,
        temperature=1200.0,
        atmosphere_dict=atmosphere_dict,
        surface_material="SiO2",
        gsi_model="sesam"
    )
    
    print(f"  Drag coefficient: {result.drag_coefficient:.4f}")
    print(f"  Projected area: {result.projected_area:.4f} m²")
    print()
    
    # Plate drag calculation  
    print("Plate Drag (convenience function):")
    print("-" * 34)
    
    result = calculate_plate_drag(
        area=1.2,
        pitch_deg=30.0,
        velocity=7750.0,
        temperature=800.0,
        atmosphere_dict=atmosphere_dict,
        surface_material="aluminum",
        gsi_model="laboratory"
    )
    
    print(f"  Drag coefficient: {result.drag_coefficient:.4f}")
    print(f"  Projected area: {result.projected_area:.4f} m²")
    print()


def example_legacy_compatibility():
    """Demonstrate backward compatibility with legacy MAIN function."""
    print("=== Legacy Compatibility ===\n")
    
    print("Using original MAIN function interface:")
    print("-" * 40)
    
    # Call the original MAIN function with the same interface
    CD_status, CD, Aout, Fcoef, alpha_out = MAIN(
        obj_type=GeometryType.SPHERE,    # 1 = sphere
        D=1.2,                           # diameter [m]
        L=0.0,                           # length (not used for sphere)
        A=0.0,                           # area (not used for sphere)
        Phi=0.0,                         # pitch angle [deg]
        Theta=0.0,                       # sideslip angle [deg]
        Ta=1200.0,                       # temperature [K]
        Va=7800.0,                       # velocity [m/s]
        n_O=1e11,                        # atomic oxygen density
        n_O2=1e6,                        # molecular oxygen density
        n_N2=1e6,                        # molecular nitrogen density
        n_He=1e6,                        # helium density
        n_H=1e4,                         # atomic hydrogen density
        GSI_model=GSIModelType.SESAM,    # -1 = SESAM model
        alpha=0.8,                       # fixed accommodation (not used for SESAM)
        m_s=65.0,                        # surface mass [amu]
        POSVEL=np.array([]).T,           # position/velocity array (empty for single point)
        fnamesurf=""                     # surface filename (not used for sphere)
    )
    
    print(f"  Status: {CD_status}")
    print(f"  Drag coefficient: {CD[0, 0]:.4f}")
    print(f"  Projected area: {Aout[0, 0]:.4f} m²")
    print(f"  Force coefficient: {Fcoef[0, 0]:.4f} m²")
    print(f"  Energy accommodation: {alpha_out[0]:.4f}")
    print()


def example_multi_point_calculation():
    """Demonstrate multi-point calculations."""
    print("=== Multi-Point Calculations ===\n")
    
    print("Drag vs. Velocity:")
    print("-" * 20)
    
    # Base parameters
    base_params = CalculationParameters(
        geometry_type="sphere",
        diameter=1.0,
        temperature=1000.0,
        n_o=1e11,
        n_o2=1e6,
        surface_material="SiO2",
        gsi_model="sesam"
    )
    
    # Variable parameters (different velocities)
    velocities = [6000, 7000, 7500, 8000, 8500]  # m/s
    variable_params = [{'velocity': v} for v in velocities]
    
    # Calculate
    calculator = DragCalculator()
    results = calculator.calculate_multi_point(base_params, variable_params)
    
    for i, result in enumerate(results):
        print(f"  V = {velocities[i]:4d} m/s: CD = {result.drag_coefficient:.4f}, "
              f"α = {result.energy_accommodation:.4f}")
    
    print()
    
    print("Drag vs. Temperature:")
    print("-" * 21)
    
    # Variable parameters (different temperatures)
    temperatures = [600, 800, 1000, 1200, 1400]  # K
    variable_params = [{'temperature': t} for t in temperatures]
    
    results = calculator.calculate_multi_point(base_params, variable_params)
    
    for i, result in enumerate(results):
        print(f"  T = {temperatures[i]:4d} K: CD = {result.drag_coefficient:.4f}, "
              f"α = {result.energy_accommodation:.4f}")
    
    print()


def example_error_handling():
    """Demonstrate error handling and validation."""
    print("=== Error Handling ===\n")
    
    print("Testing parameter validation:")
    print("-" * 30)
    
    calculator = DragCalculator()
    
    # Test invalid parameters
    test_cases = [
        {
            'description': 'Negative diameter',
            'params': CalculationParameters(
                geometry_type="sphere",
                diameter=-1.0,
                velocity=7800.0,
                temperature=1000.0,
                n_o=1e11
            )
        },
        {
            'description': 'Zero velocity',
            'params': CalculationParameters(
                geometry_type="sphere", 
                diameter=1.0,
                velocity=0.0,
                temperature=1000.0,
                n_o=1e11
            )
        },
        {
            'description': 'Invalid material',
            'params': CalculationParameters(
                geometry_type="sphere",
                diameter=1.0,
                velocity=7800.0,
                temperature=1000.0,
                n_o=1e11,
                surface_material="unobtainium"
            )
        }
    ]
    
    for test_case in test_cases:
        try:
            calculator.calculate_drag(test_case['params'])
            print(f"  {test_case['description']}: Unexpectedly succeeded")
        except Exception as e:
            print(f"  {test_case['description']}: {type(e).__name__} - {e}")
    
    print()


if __name__ == "__main__":
    print("VECTOR Drag Calculation Examples")
    print("=" * 50)
    print()
    
    # Run examples
    example_modern_api()
    example_convenience_functions() 
    example_legacy_compatibility()
    example_multi_point_calculation()
    example_error_handling()
    
    print("Examples completed successfully!")
    print("\nFor more information, see the documentation or:")
    print("  - vector_python.DragCalculator for the main API")
    print("  - vector_python.MAIN for legacy compatibility")
    print("  - vector_python.calculate_sphere_drag for simple sphere calculations")
    print("  - vector_python.calculate_plate_drag for simple plate calculations")