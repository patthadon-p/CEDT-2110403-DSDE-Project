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
from .FuzzyUtils import fuzzy_match, normalize
from .GeographicUtils import load_geographic_data, save_geographic_data
from .ProvinceUtils import load_province_whitelist
from .StatusUtils import load_status_mapping
from .DatetimeUtils import get_buddhist_year_last_two_digits

# Define what gets imported with 'from utils import *'
__all__ = [
    # Functions
    # DistrictSubdistrictUtils.py
    "load_bangkok_official_area_names",
    # FuzzyUtils.py
    "fuzzy_match",
    "normalize",
    # GeographicUtils.py
    "load_geographic_data",
    "save_geographic_data",
    # ProvinceUtils.py
    "load_province_whitelist",
    # StatusUtils.py
    "load_status_mapping",
    "get_buddhist_year_last_two_digits",
]
