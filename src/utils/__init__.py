"""
Utils Module

This module contains utility functions for data processing and analysis
for the CEDT-2110403-DSDE-Project.

It provides direct access to various helper functions for configuration handling,
datetime conversion, text normalization, geographic data management, and
predefined mapping lookups.

Functions
---------
get_configs_path
    Retrieves the absolute path to the configuration directory.
get_data_dir
    Retrieves the absolute path to the main data directory.
read_config_path
    Reads a specific file path from a general configuration file.
get_buddhist_year
    Calculates and returns the current year in the Buddhist calendar.
load_bangkok_official_area_names
    Loads the official list of Bangkok district and subdistrict names.
fuzzy_match
    Performs fuzzy string matching against a list of targets using caching.
normalize
    Applies standard text normalization rules (e.g., lowercase, remove extra spaces).
load_geographic_data
    Loads geographic boundary data (GeoDataFrame) from a specified path.
save_geographic_data
    Saves a geographic boundary data (GeoDataFrame) to the data directory.
load_province_whitelist
    Loads the mapping dictionary for province name standardization.
load_status_mapping
    Loads the mapping dictionary for state-to-status standardization.

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
from .ConfigUtils import get_configs_path, get_data_dir, read_config_path
from .DatetimeUtils import get_buddhist_year
from .DistrictSubdistrictUtils import load_bangkok_official_area_names
from .FuzzyUtils import fuzzy_match, normalize
from .GeographicUtils import load_geographic_data, save_geographic_data
from .ProvinceUtils import load_province_whitelist
from .StatusUtils import load_status_mapping

# Define what gets imported with 'from utils import *'
__all__ = [
    # Functions
    # ConfigUtils.py
    "get_configs_path",
    "get_data_dir",
    "read_config_path",
    # DatetimeUtils.py
    "get_buddhist_year",
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
]
