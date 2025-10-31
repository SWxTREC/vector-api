"""
Utility functions for mathematical operations in VECTOR calculations.

This module provides common mathematical functions and utilities used
throughout the drag coefficient calculations.
"""

import numpy as np
from typing import Union, Tuple
from .constants import Tolerances


def safe_normalize(vector: np.ndarray) -> np.ndarray:
    """
    Safely normalize a vector, handling zero-length cases.
    
    Args:
        vector: Input vector to normalize
        
    Returns:
        Normalized vector
        
    Raises:
        ValueError: If vector is all zeros
    """
    norm = np.linalg.norm(vector)
    if norm < Tolerances.FLOAT_EPS:
        raise ValueError("Cannot normalize zero-length vector")
    return vector / norm


def ensure_non_zero_velocity(velocity: np.ndarray) -> np.ndarray:
    """
    Ensure velocity vector is not zero by adding small perturbations.
    
    Args:
        velocity: Input velocity vector
        
    Returns:
        Velocity vector with guaranteed non-zero magnitude
    """
    if np.linalg.norm(velocity) < Tolerances.ZERO_VELOCITY_THRESHOLD:
        return velocity + np.array([
            Tolerances.FLOAT_EPS * 2,
            -Tolerances.FLOAT_EPS * 2,
            Tolerances.FLOAT_EPS * 2
        ])
    return velocity


def polygon_area(x_coords: np.ndarray, y_coords: np.ndarray) -> float:
    """
    Calculate the area of a polygon using the shoelace formula.
    
    Args:
        x_coords: X coordinates of polygon vertices
        y_coords: Y coordinates of polygon vertices
        
    Returns:
        Area of the polygon
    """
    correction = x_coords[-1] * y_coords[0] - y_coords[-1] * x_coords[0]
    main_area = np.dot(x_coords[:-1], y_coords[1:]) - np.dot(y_coords[:-1], x_coords[1:])
    return 0.5 * np.abs(main_area + correction)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def safe_divide(numerator: Union[float, np.ndarray], 
                denominator: Union[float, np.ndarray],
                default: float = 0.0) -> Union[float, np.ndarray]:
    """
    Safely divide two values, handling division by zero.
    
    Args:
        numerator: Numerator value(s)
        denominator: Denominator value(s)
        default: Default value to return if denominator is zero
        
    Returns:
        Division result or default value
    """
    if isinstance(denominator, np.ndarray):
        result = np.where(np.abs(denominator) > Tolerances.FLOAT_EPS,
                         numerator / denominator, default)
        return result
    else:
        if abs(denominator) > Tolerances.FLOAT_EPS:
            return numerator / denominator
        return default


def triangle_properties(vertices: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Calculate properties of a triangle from its vertices.
    
    Args:
        vertices: Array of shape (3, 3) containing the three vertices
        
    Returns:
        Tuple of (normal_vector, centroid, area)
    """
    # Get vertices
    a, b, c = vertices[0], vertices[1], vertices[2]
    
    # Calculate edge vectors
    edge1 = b - a
    edge2 = c - a
    
    # Calculate normal vector using cross product
    normal = np.cross(edge1, edge2)
    
    # Normalize the normal vector
    normal = safe_normalize(normal)
    
    # Calculate centroid
    centroid = (a + b + c) / 3
    
    # Calculate area using cross product magnitude
    area = 0.5 * np.linalg.norm(np.cross(edge1, edge2))
    
    return normal, centroid, area


def interpolate_material_property(angle_degrees: float, 
                                angles: list, 
                                values: list,
                                bounds: Tuple[float, float] = (0.0, 1.0)) -> float:
    """
    Interpolate material property based on incident angle.
    
    Args:
        angle_degrees: Incident angle in degrees
        angles: List of reference angles
        values: List of property values at reference angles
        bounds: Tuple of (min_value, max_value) for clamping
        
    Returns:
        Interpolated property value
    """
    interpolated = np.interp(angle_degrees, angles, values, left=0, right=1)
    return clamp(interpolated, bounds[0], bounds[1])