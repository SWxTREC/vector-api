"""
Geometry module for VECTOR drag calculations.

This module provides classes to handle different satellite geometries and their
geometric properties for drag calculations.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Union
from pathlib import Path

from .exceptions import GeometryError, ValidationError, FileFormatError
from .utils import triangle_properties, polygon_area, ensure_non_zero_velocity
from .constants import Tolerances


class Geometry(ABC):
    """Abstract base class for all geometry types."""
    
    def __init__(self, name: str):
        """
        Initialize geometry.
        
        Args:
            name: Name/description of the geometry
        """
        self.name = name
    
    @abstractmethod
    def projected_area(self, pitch_deg: float = 0.0, sideslip_deg: float = 0.0) -> float:
        """
        Calculate the projected area perpendicular to flow direction.
        
        Args:
            pitch_deg: Pitch angle in degrees
            sideslip_deg: Sideslip angle in degrees
            
        Returns:
            Projected area in m²
        """
        pass
    
    @abstractmethod
    def reference_area(self) -> float:
        """
        Get the reference area for this geometry.
        
        Returns:
            Reference area in m²
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}')"


class SphereGeometry(Geometry):
    """Spherical satellite geometry."""
    
    def __init__(self, diameter: float, name: str = "Sphere"):
        """
        Initialize sphere geometry.
        
        Args:
            diameter: Sphere diameter in meters
            name: Name/description of the geometry
        """
        super().__init__(name)
        
        if diameter <= 0:
            raise ValidationError("Diameter must be positive", "diameter", diameter)
        
        self.diameter = diameter
        self.radius = diameter / 2
    
    def projected_area(self, pitch_deg: float = 0.0, sideslip_deg: float = 0.0) -> float:
        """
        Calculate projected area of sphere (independent of orientation).
        
        Args:
            pitch_deg: Ignored for sphere
            sideslip_deg: Ignored for sphere
            
        Returns:
            Projected area (π * r²)
        """
        return np.pi * self.radius ** 2
    
    def reference_area(self) -> float:
        """Reference area is the cross-sectional area."""
        return self.projected_area()
    
    def surface_area(self) -> float:
        """Calculate total surface area of sphere."""
        return 4 * np.pi * self.radius ** 2
    
    def volume(self) -> float:
        """Calculate volume of sphere."""
        return (4/3) * np.pi * self.radius ** 3


class PlateGeometry(Geometry):
    """Flat plate satellite geometry."""
    
    def __init__(self, area: float, name: str = "Plate"):
        """
        Initialize plate geometry.
        
        Args:
            area: Plate area in m²
            name: Name/description of the geometry
        """
        super().__init__(name)
        
        if area <= 0:
            raise ValidationError("Area must be positive", "area", area)
        
        self.area = area
    
    def projected_area(self, pitch_deg: float = 0.0, sideslip_deg: float = 0.0) -> float:
        """
        Calculate projected area of plate based on pitch angle.
        
        Args:
            pitch_deg: Pitch angle in degrees
            sideslip_deg: Ignored for plate
            
        Returns:
            Projected area (area * |cos(pitch)|)
        """
        pitch_rad = np.radians(pitch_deg)
        return self.area * abs(np.cos(pitch_rad))
    
    def reference_area(self) -> float:
        """Reference area is the plate area."""
        return self.area


class CylinderGeometry(Geometry):
    """Cylindrical satellite geometry."""
    
    def __init__(self, diameter: float, length: float, name: str = "Cylinder"):
        """
        Initialize cylinder geometry.
        
        Args:
            diameter: Cylinder diameter in meters
            length: Cylinder length in meters
            name: Name/description of the geometry
        """
        super().__init__(name)
        
        if diameter <= 0:
            raise ValidationError("Diameter must be positive", "diameter", diameter)
        if length <= 0:
            raise ValidationError("Length must be positive", "length", length)
        
        self.diameter = diameter
        self.length = length
        self.radius = diameter / 2
    
    def projected_area(self, pitch_deg: float = 0.0, sideslip_deg: float = 0.0) -> float:
        """
        Calculate oblique projection area of cylinder.
        
        Args:
            pitch_deg: Pitch angle in degrees
            sideslip_deg: Ignored for cylinder
            
        Returns:
            Oblique projected area in m²
        """
        pitch_rad = np.radians(abs(pitch_deg))
        
        # Handle edge cases
        if pitch_rad == 0:
            pitch_rad = np.nextafter(0, 1)
        
        # Ellipse parameters for oblique projection
        a = self.radius  # Semi-major axis
        b = self.diameter * np.cos(pitch_rad) / 2  # Semi-minor axis
        ellipse_area = a * b * np.pi
        
        # Calculate projected area components
        y = self.length * np.sin(pitch_rad) / 2
        
        if y >= b:
            # Long cylinder case
            front_area = ellipse_area
            back_area = ellipse_area
            mid_area = self.length * np.sin(pitch_rad) * self.diameter - ellipse_area
        else:
            # Short cylinder case
            phi = np.arcsin(y / b)
            
            # Sector area calculation
            sector_area = (a * b) * (np.arctan((b / a) * np.tan(np.pi / 2)) - 
                                   np.arctan((b / a) * np.tan(phi)))
            
            # Triangle area
            base = 2 * y / np.tan(phi)
            triangle_area = 0.5 * base * y
            
            # Segment area
            segment_area = sector_area - triangle_area
            
            front_area = ellipse_area
            back_area = ellipse_area - 2 * segment_area
            mid_area = (self.length * np.sin(pitch_rad) * self.diameter - 
                       (ellipse_area - 2 * segment_area))
        
        return front_area + back_area + mid_area
    
    def reference_area(self) -> float:
        """Reference area is the circular cross-section."""
        return np.pi * self.radius ** 2
    
    def surface_area(self) -> float:
        """Calculate total surface area of cylinder."""
        return 2 * np.pi * self.radius * self.length + 2 * np.pi * self.radius ** 2
    
    def volume(self) -> float:
        """Calculate volume of cylinder."""
        return np.pi * self.radius ** 2 * self.length


class TriangleMesh:
    """Represents a triangular mesh for complex geometries."""
    
    def __init__(self, vertices: np.ndarray, triangles: np.ndarray):
        """
        Initialize triangle mesh.
        
        Args:
            vertices: Array of vertex coordinates (N, 3)
            triangles: Array of triangle vertex indices (M, 3)
        """
        self.vertices = np.array(vertices, dtype=float)
        self.triangles = np.array(triangles, dtype=int)
        
        self._validate_mesh()
        self._precompute_properties()
    
    def _validate_mesh(self):
        """Validate mesh data."""
        if self.vertices.shape[1] != 3:
            raise GeometryError("Vertices must have 3 coordinates (x, y, z)")
        
        if self.triangles.shape[1] != 3:
            raise GeometryError("Triangles must have 3 vertex indices")
        
        max_index = np.max(self.triangles)
        if max_index >= len(self.vertices):
            raise GeometryError(f"Triangle index {max_index} exceeds vertex count {len(self.vertices)}")
    
    def _precompute_properties(self):
        """Precompute triangle properties."""
        n_triangles = len(self.triangles)
        
        self.triangle_normals = np.zeros((n_triangles, 3))
        self.triangle_centroids = np.zeros((n_triangles, 3))
        self.triangle_areas = np.zeros(n_triangles)
        
        for i, tri_indices in enumerate(self.triangles):
            tri_vertices = self.vertices[tri_indices]
            normal, centroid, area = triangle_properties(tri_vertices)
            
            self.triangle_normals[i] = normal
            self.triangle_centroids[i] = centroid
            self.triangle_areas[i] = area
    
    def get_triangle_data(self, index: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """
        Get data for a specific triangle.
        
        Args:
            index: Triangle index
            
        Returns:
            Tuple of (vertices, normal, centroid, area)
        """
        if index >= len(self.triangles):
            raise GeometryError(f"Triangle index {index} out of range")
        
        tri_vertices = self.vertices[self.triangles[index]]
        return (tri_vertices, 
                self.triangle_normals[index],
                self.triangle_centroids[index],
                self.triangle_areas[index])
    
    @property
    def num_triangles(self) -> int:
        """Number of triangles in mesh."""
        return len(self.triangles)
    
    @property
    def total_surface_area(self) -> float:
        """Total surface area of mesh."""
        return np.sum(self.triangle_areas)


class CustomGeometry(Geometry):
    """Custom satellite geometry defined by triangular mesh."""
    
    def __init__(self, mesh: TriangleMesh, name: str = "Custom"):
        """
        Initialize custom geometry.
        
        Args:
            mesh: Triangular mesh defining the geometry
            name: Name/description of the geometry
        """
        super().__init__(name)
        self.mesh = mesh
    
    @classmethod
    def from_file(cls, filepath: Union[str, Path], name: Optional[str] = None) -> 'CustomGeometry':
        """
        Load custom geometry from VRML file.
        
        Args:
            filepath: Path to VRML (.wrl) file
            name: Optional name for the geometry
            
        Returns:
            CustomGeometry instance
        """
        filepath = Path(filepath)
        if name is None:
            name = filepath.stem
        
        try:
            triangles, vertices_x, vertices_y, vertices_z = cls._parse_vrml_file(filepath)
            
            # Combine vertex coordinates
            vertices = np.column_stack([vertices_x, vertices_y, vertices_z])
            
            # Create mesh
            mesh = TriangleMesh(vertices, triangles)
            
            return cls(mesh, name)
            
        except Exception as e:
            raise FileFormatError(f"Failed to parse VRML file {filepath}: {e}")
    
    @staticmethod
    def _parse_vrml_file(filepath: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Parse VRML file to extract geometry data.
        
        Args:
            filepath: Path to VRML file
            
        Returns:
            Tuple of (triangles, x_coords, y_coords, z_coords)
        """
        # This would need proper VRML parsing implementation
        # For now, this is a placeholder that will be implemented later
        raise NotImplementedError(f"VRML parsing not yet implemented in refactored version for {filepath}")
    
    def projected_area(self, pitch_deg: float = 0.0, sideslip_deg: float = 0.0) -> float:
        """
        Calculate projected area based on viewing direction.
        
        Args:
            pitch_deg: Pitch angle in degrees
            sideslip_deg: Sideslip angle in degrees
            
        Returns:
            Projected area in m²
        """
        # Convert angles to velocity vector
        pitch_rad = np.radians(pitch_deg)
        sideslip_rad = np.radians(sideslip_deg)
        
        v_horizontal = np.cos(pitch_rad)
        v_z = np.sin(pitch_rad)
        v_x = v_horizontal * np.cos(sideslip_rad)
        v_y = v_horizontal * np.sin(sideslip_rad)
        
        velocity = np.array([v_x, v_y, v_z])
        velocity = ensure_non_zero_velocity(velocity)
        
        # Calculate projected area for each visible triangle
        total_projected_area = 0.0
        
        for i in range(self.mesh.num_triangles):
            vertices, normal, _, _ = self.mesh.get_triangle_data(i)
            
            # Check if triangle faces the flow
            if np.dot(velocity, normal) < 0:  # Facing into flow
                # Project triangle onto plane perpendicular to velocity
                projected_vertices = self._project_triangle(vertices, velocity)
                area = polygon_area(projected_vertices[:, 0], projected_vertices[:, 1])
                total_projected_area += area
        
        return total_projected_area
    
    def _project_triangle(self, vertices: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        """
        Project triangle vertices onto plane perpendicular to velocity.
        
        Args:
            vertices: Triangle vertices (3, 3)
            velocity: Velocity vector (3,)
            
        Returns:
            Projected vertices in 2D coordinate system (3, 2)
        """
        velocity_unit = velocity / np.linalg.norm(velocity)
        
        # Create orthonormal basis for projection plane
        z_axis = np.array([0, 0, 1])
        j_hat = np.cross(velocity_unit, z_axis)
        
        if np.linalg.norm(j_hat) < Tolerances.FLOAT_EPS:
            # Velocity is parallel to z-axis, use different reference
            z_axis = np.array([1, 0, 0])
            j_hat = np.cross(velocity_unit, z_axis)
        
        j_hat = j_hat / np.linalg.norm(j_hat)
        k_hat = np.cross(j_hat, velocity_unit)
        k_hat = k_hat / np.linalg.norm(k_hat)
        
        # Project vertices onto 2D plane
        projected = np.zeros((3, 2))
        for i, vertex in enumerate(vertices):
            projected[i, 0] = np.dot(vertex, j_hat)
            projected[i, 1] = np.dot(vertex, k_hat)
        
        return projected
    
    def reference_area(self) -> float:
        """Reference area is the total surface area."""
        return self.mesh.total_surface_area


def create_geometry(geometry_type: str, **kwargs) -> Geometry:
    """
    Factory function to create geometry objects.
    
    Args:
        geometry_type: Type of geometry ('sphere', 'plate', 'cylinder', 'custom')
        **kwargs: Geometry-specific parameters
        
    Returns:
        Geometry instance
    """
    geometry_type = geometry_type.lower().strip()
    
    if geometry_type == 'sphere':
        return SphereGeometry(**kwargs)
    elif geometry_type == 'plate':
        return PlateGeometry(**kwargs)
    elif geometry_type == 'cylinder':
        return CylinderGeometry(**kwargs)
    elif geometry_type == 'custom':
        return CustomGeometry(**kwargs)
    else:
        raise GeometryError(f"Unknown geometry type: {geometry_type}. "
                          f"Available: sphere, plate, cylinder, custom")