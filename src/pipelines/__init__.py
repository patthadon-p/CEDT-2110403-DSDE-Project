"""
Pipelines Module

This module contains data transformation and processing pipelines
for the CEDT-2110403-DSDE-Project.

Usage:
    # Import everything
    from pipelines import *

    # Import specific classes
    from pipelines import ProvinceTransformer

    # Access directly
    import pipelines
    transformer = pipelines.ProvinceTransformer()
"""

# Import specific classes and functions for direct access
from .AddressTransformer import AddressTransformer
from .CleansingPipeline import CleansingPipeline
from .CoordinateTransformer import CoordinateTransformer
from .DateTransformer import DateTransformer
from .DistrictSubdistrictTransformer import DistrictSubdistrictTransformer
from .ProvinceTransformer import ProvinceTransformer
from .StateToStatusTransformer import StateToStatusTransformer

# Define what gets imported with 'from pipelines import *'
__all__ = [
    # Classes
    "AddressTransformer",
    "CleansingPipeline",
    "CoordinateTransformer",
    "DateTransformer",
    "DistrictSubdistrictTransformer",
    "ProvinceTransformer",
    "StateToStatusTransformer",
]
