"""
Backward compatibility layer for VECTOR.

This module provides the original MAIN function interface while using
the new refactored architecture internally. This allows existing code
to continue working without modification.
"""

import numpy as np
from typing import Tuple

from .drag_calculator import DragCalculator, CalculationParameters
from .constants import GeometryType, GSIModel


def MAIN(obj_type: int, 
         D: float, 
         L: float, 
         A: float, 
         Phi: float, 
         Theta: float, 
         Ta: float, 
         Va: float, 
         n_O: float, 
         n_O2: float, 
         n_N2: float, 
         n_He: float, 
         n_H: float, 
         GSI_model: int, 
         alpha: float, 
         m_s: float, 
         POSVEL: np.ndarray, 
         fnamesurf: str) -> Tuple[int, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Original MAIN function interface for backward compatibility.
    
    This function maintains the exact same interface as the original MATLAB-derived
    implementation but uses the new refactored architecture internally.
    
    Args:
        obj_type: Object type (1=sphere, 2=plate, 3=cylinder, 4=custom)
        D: Diameter [m]
        L: Length [m] 
        A: Area [m²]
        Phi: Pitch angle [degrees]
        Theta: Sideslip angle [degrees]
        Ta: Atmospheric temperature [K]
        Va: Velocity magnitude [m/s]
        n_O: Atomic oxygen number density [particles/m³]
        n_O2: Molecular oxygen number density [particles/m³]
        n_N2: Molecular nitrogen number density [particles/m³]
        n_He: Helium number density [particles/m³]
        n_H: Atomic hydrogen number density [particles/m³]
        GSI_model: GSI model type (-1=SESAM, 0=fixed, 2=Goodman, 3=CLL, 4=laboratory)
        alpha: Fixed accommodation coefficient (for GSI_model=0)
        m_s: Surface mass [amu]
        POSVEL: Position/velocity array (not used in single-point mode)
        fnamesurf: Surface file name (for custom geometry)
        
    Returns:
        Tuple of (CD_status, CD, Aout, Fcoef, alpha_out)
        - CD_status: Status code (1 = success)
        - CD: Drag coefficient array
        - Aout: Projected area array [m²]
        - Fcoef: Force coefficient array [m²]
        - alpha_out: Energy accommodation coefficient array
    """
    try:
        # Map object type to geometry type
        geometry_type_map = {
            GeometryType.SPHERE: "sphere",
            GeometryType.PLATE: "plate", 
            GeometryType.CYLINDER: "cylinder",
            GeometryType.CUSTOM: "custom"
        }
        
        if obj_type not in geometry_type_map:
            raise ValueError(f"Invalid object type: {obj_type}")
        
        geometry_type = geometry_type_map[obj_type]
        
        # Map GSI model type
        gsi_model_map = {
            GSIModel.SESAM: "sesam",
            GSIModel.FIXED: "fixed",
            GSIModel.GOODMAN: "goodman", 
            GSIModel.CLL_QUASI_SPECULAR: "cll",
            GSIModel.LABORATORY_DERIVED: "laboratory"
        }
        
        if GSI_model not in gsi_model_map:
            raise ValueError(f"Invalid GSI model: {GSI_model}")
        
        gsi_model = gsi_model_map[GSI_model]
        
        # Create calculation parameters
        params = CalculationParameters(
            geometry_type=geometry_type,
            diameter=D if obj_type in [GeometryType.SPHERE, GeometryType.CYLINDER] else None,
            length=L if obj_type == GeometryType.CYLINDER else None,
            area=A if obj_type == GeometryType.PLATE else None,
            geometry_file=fnamesurf if obj_type == GeometryType.CUSTOM else None,
            pitch_deg=Phi,
            sideslip_deg=Theta,
            velocity=Va,
            temperature=Ta,
            n_n2=n_N2,
            n_o2=n_O2,
            n_o=n_O,
            n_he=n_He,
            n_h=n_H,
            surface_mass_amu=m_s,
            gsi_model=gsi_model,
            fixed_accommodation=alpha if GSI_model == GSIModel.FIXED else None
        )
        
        # Calculate drag using new architecture
        calculator = DragCalculator()
        result = calculator.calculate_drag(params)
        
        # Format results to match original interface
        CD_status = 1  # Success
        CD = np.array([[result.drag_coefficient]])
        Aout = np.array([[result.projected_area]])
        Fcoef = np.array([[result.force_coefficient]])
        alpha_out = np.array([result.energy_accommodation])
        
        return CD_status, CD, Aout, Fcoef, alpha_out
        
    except Exception as e:
        # Return error status with default values
        print(f"Error in MAIN function: {e}")
        CD_status = 0  # Error
        CD = np.array([[-99.0]])
        Aout = np.array([[-99.0]])
        Fcoef = np.array([[-99.0]])
        alpha_out = np.array([-99.0])
        
        return CD_status, CD, Aout, Fcoef, alpha_out


# Additional compatibility functions for common usage patterns
def calculate_sphere_drag_legacy(diameter: float,
                                velocity: float, 
                                temperature: float,
                                n_o: float,
                                n_o2: float = 0.0,
                                n_n2: float = 0.0,
                                n_he: float = 0.0,
                                n_h: float = 0.0,
                                surface_mass: float = 65.0,
                                gsi_model: int = GSIModel.SESAM,
                                fixed_accommodation: float = 0.8) -> dict:
    """Legacy sphere drag calculation with simplified interface."""
    
    CD_status, CD, Aout, Fcoef, alpha_out = MAIN(
        obj_type=GeometryType.SPHERE,
        D=diameter,
        L=0.0,
        A=0.0,
        Phi=0.0,
        Theta=0.0,
        Ta=temperature,
        Va=velocity,
        n_O=n_o,
        n_O2=n_o2,
        n_N2=n_n2,
        n_He=n_he,
        n_H=n_h,
        GSI_model=gsi_model,
        alpha=fixed_accommodation,
        m_s=surface_mass,
        POSVEL=np.array([]).T,
        fnamesurf=""
    )
    
    return {
        'status': CD_status,
        'drag_coefficient': CD[0, 0],
        'projected_area': Aout[0, 0],
        'force_coefficient': Fcoef[0, 0],
        'energy_accommodation': alpha_out[0]
    }


def calculate_plate_drag_legacy(area: float,
                               pitch_deg: float,
                               velocity: float,
                               temperature: float,
                               n_o: float,
                               n_o2: float = 0.0,
                               n_n2: float = 0.0,
                               n_he: float = 0.0,
                               n_h: float = 0.0,
                               surface_mass: float = 65.0,
                               gsi_model: int = GSIModel.SESAM,
                               fixed_accommodation: float = 0.8) -> dict:
    """Legacy plate drag calculation with simplified interface."""
    
    CD_status, CD, Aout, Fcoef, alpha_out = MAIN(
        obj_type=GeometryType.PLATE,
        D=0.0,
        L=0.0,
        A=area,
        Phi=pitch_deg,
        Theta=0.0,
        Ta=temperature,
        Va=velocity,
        n_O=n_o,
        n_O2=n_o2,
        n_N2=n_n2,
        n_He=n_he,
        n_H=n_h,
        GSI_model=gsi_model,
        alpha=fixed_accommodation,
        m_s=surface_mass,
        POSVEL=np.array([]).T,
        fnamesurf=""
    )
    
    return {
        'status': CD_status,
        'drag_coefficient': CD[0, 0], 
        'projected_area': Aout[0, 0],
        'force_coefficient': Fcoef[0, 0],
        'energy_accommodation': alpha_out[0]
    }