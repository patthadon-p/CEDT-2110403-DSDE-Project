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
from . import pipelines, utils, scrapping

# Import specific items to make them available at package level
# from .pipelines import *
# from .utils import *

# Define what gets imported with 'from src import *'
__all__ = [
    # Modules
    "pipelines",
    "utils",
    "scrapping",
]
