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

# Import necessary modules
from pathlib import Path

# Import specific classes and functions for direct access
from .DistrictSubdistrictUtils import load_bangkok_official_area_names
from .GeographicUtils import load_geographic_data
from .ProvinceUtils import load_province_whitelist
from .StatusUtils import load_status_mapping

# Define the path to the configs directory
base_dir = Path(__file__).resolve().parents[2]
configs_path = base_dir / "configs" / "configs.yaml"
configs_path = str(configs_path)

# Define what gets imported with 'from utils import *'
__all__ = [
    # Functions
    "load_bangkok_official_area_names",
    "load_geographic_data",
    "load_province_whitelist",
    "load_status_mapping",
]
