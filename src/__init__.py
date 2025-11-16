"""
CEDT-2110403-DSDE-Project Source Package

This package contains data processing pipelines and utilities for the
Data Science and Data Engineering project.

Usage:
    # Import everything
    from src import *

    # Import specific modules
    from src.pipelines import ProvinceTransformer
    from src.utils import load_province_whitelist

    # Access modules directly
    import src
    transformer = src.pipelines.ProvinceTransformer()
"""

# Import all submodules and their contents
from . import pipelines, utils

# Import specific classes and functions for direct access
from .pipelines import (
    DistrictSubdistrictTransformer,
    ProvinceTransformer,
    StateToStatusTransformer,
)
from .utils import (
    load_bangkok_official_area_names,
    load_province_whitelist,
    load_status_mapping,
)

# Define what gets imported with 'from src import *'
__all__ = [
    # Modules
    "pipelines",
    "utils",
    # Classes
    "ProvinceTransformer",
    "DistrictSubdistrictTransformer",
    "StateToStatusTransformer",
    # Functions
    "load_province_whitelist",
    "load_bangkok_official_area_names",
    "load_status_mapping",
]
