"""
Custom exceptions for the VECTOR drag coefficient calculation package.

This module defines specific exception types to provide clear error reporting
and better debugging experience for users of the VECTOR package.
"""

from typing import Any, Optional


class VectorError(Exception):
    """Base exception for all VECTOR package errors."""
    pass


class ValidationError(VectorError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, parameter: Optional[str] = None, value: Optional[Any] = None):
        self.parameter = parameter
        self.value = value
        
        if parameter and value is not None:
            super().__init__(f"Validation error for parameter '{parameter}': {message} (got {value})")
        else:
            super().__init__(message)


class GeometryError(VectorError):
    """Raised when geometry-related operations fail."""
    pass


class MaterialError(VectorError):
    """Raised when material property operations fail."""
    pass


class AtmosphereError(VectorError):
    """Raised when atmospheric composition operations fail."""
    pass


class CalculationError(VectorError):
    """Raised when drag coefficient calculations fail."""
    pass


class GSIModelError(VectorError):
    """Raised when gas-surface interaction model operations fail."""
    pass


class FileFormatError(VectorError):
    """Raised when geometry file parsing fails."""
    pass