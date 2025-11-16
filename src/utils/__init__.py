"""
Utils Module

This module contains utility functions for data processing and analysis
for the CEDT-2110403-DSDE-Project.

Usage:
    # Import everything
    from utils import *

    # Import specific functions
    from utils import load_province_whitelist

    # Access directly
    import utils
    whitelist = utils.load_province_whitelist()
"""

# Import specific classes and functions for direct access
from .DistrictSubdistrictUtils import load_bangkok_official_area_names
from .ProvinceUtils import load_province_whitelist
from .StatusUtils import load_status_mapping

# Define what gets imported with 'from utils import *'
__all__ = [
    # Functions
    "load_province_whitelist",
    "load_bangkok_official_area_names",
    "load_status_mapping",
]
