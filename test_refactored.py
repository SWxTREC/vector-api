"""
Simple test to verify the refactored VECTOR package works correctly.
"""

import sys
import traceback
from vector_python import (
    DragCalculator, 
    CalculationParameters,
    calculate_sphere_drag,
    MAIN,
    GeometryType,
    GSIModelType
)
import numpy as np


def test_modern_api():
    """Test the modern Pythonic API."""
    print("Testing modern API...")
    
    try:
        params = CalculationParameters(
            geometry_type="sphere",
            diameter=1.2,
            velocity=7800.0,
            temperature=1200.0,
            n_o=1e11,
            n_o2=1e6,
            n_n2=1e6,
            surface_material="SiO2",
            gsi_model="sesam"
        )
        
        calculator = DragCalculator()
        result = calculator.calculate_drag(params)
        
        print(f"  ✓ Drag coefficient: {result.drag_coefficient:.4f}")
        print(f"  ✓ Projected area: {result.projected_area:.4f} m²")
        print(f"  ✓ Energy accommodation: {result.energy_accommodation:.4f}")
        
        # Basic sanity checks
        assert 0 < result.drag_coefficient < 10, "Drag coefficient out of reasonable range"
        assert result.projected_area > 0, "Projected area should be positive"
        assert 0 <= result.energy_accommodation <= 1, "Accommodation should be between 0 and 1"
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_convenience_function():
    """Test convenience functions."""
    print("Testing convenience functions...")
    
    try:
        atmosphere = {
            'O': 1e11,
            'O2': 1e6,
            'N2': 1e6
        }
        
        result = calculate_sphere_drag(
            diameter=1.2,
            velocity=7800.0,
            temperature=1200.0,
            atmosphere_dict=atmosphere,
            surface_material="SiO2",
            gsi_model="sesam"
        )
        
        print(f"  ✓ Convenience function drag coefficient: {result.drag_coefficient:.4f}")
        
        # Should give similar result to direct API
        assert 0 < result.drag_coefficient < 10, "Drag coefficient out of reasonable range"
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_legacy_compatibility():
    """Test backward compatibility with legacy MAIN function."""
    print("Testing legacy compatibility...")
    
    try:
        CD_status, CD, Aout, Fcoef, alpha_out = MAIN(
            obj_type=GeometryType.SPHERE,
            D=1.2,
            L=0.0,
            A=0.0,
            Phi=0.0,
            Theta=0.0,
            Ta=1200.0,
            Va=7800.0,
            n_O=1e11,
            n_O2=1e6,
            n_N2=1e6,
            n_He=1e6,
            n_H=1e4,
            GSI_model=GSIModelType.SESAM,
            alpha=0.8,
            m_s=65.0,
            POSVEL=np.array([]).T,
            fnamesurf=""
        )
        
        print(f"  ✓ Legacy function status: {CD_status}")
        print(f"  ✓ Legacy drag coefficient: {CD[0, 0]:.4f}")
        print(f"  ✓ Legacy accommodation: {alpha_out[0]:.4f}")
        
        # Check status and reasonable values
        assert CD_status == 1, "Legacy function should return success status"
        assert 0 < CD[0, 0] < 10, "Legacy drag coefficient out of reasonable range"
        assert 0 <= alpha_out[0] <= 1, "Legacy accommodation should be between 0 and 1"
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        traceback.print_exc()
        return False


def test_different_geometries():
    """Test different geometry types."""
    print("Testing different geometries...")
    
    success = True
    
    # Test plate
    try:
        params = CalculationParameters(
            geometry_type="plate",
            area=1.2,
            pitch_deg=30.0,
            velocity=7750.0,
            temperature=800.0,
            n_o=1e11,
            surface_material="aluminum",
            gsi_model="goodman"
        )
        
        calculator = DragCalculator()
        result = calculator.calculate_drag(params)
        
        print(f"  ✓ Plate drag coefficient: {result.drag_coefficient:.4f}")
        assert 0 < result.drag_coefficient < 10, "Plate drag coefficient out of range"
        
    except Exception as e:
        print(f"  ✗ Plate error: {e}")
        success = False
    
    # Test cylinder
    try:
        params = CalculationParameters(
            geometry_type="cylinder",
            diameter=1.0,
            length=2.0,
            pitch_deg=15.0,
            velocity=7500.0,
            temperature=900.0,
            n_o=5e10,
            surface_material="Teflon",
            gsi_model="fixed",
            fixed_accommodation=0.7
        )
        
        result = calculator.calculate_drag(params)
        
        print(f"  ✓ Cylinder drag coefficient: {result.drag_coefficient:.4f}")
        assert 0 < result.drag_coefficient < 10, "Cylinder drag coefficient out of range"
        
    except Exception as e:
        print(f"  ✗ Cylinder error: {e}")
        success = False
    
    return success


def main():
    """Run all tests."""
    print("VECTOR Refactored Package Test")
    print("=" * 40)
    
    tests = [
        test_modern_api,
        test_convenience_function,
        test_legacy_compatibility,
        test_different_geometries
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactored package is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())