"""
Pipelines Module

This module contains data transformation and processing pipelines
for the CEDT-2110403-DSDE-Project.

It provides direct access to all major transformer classes designed
for data cleansing, standardization, and feature engineering.

Classes
-------
AddressTransformer
    Transformer for address standardization and geographic enrichment.
CleansingPipeline
    The main meta-transformer orchestrating all cleansing steps.
CoordinateTransformer
    Transformer for processing and validating geographic coordinates.
DateTransformer
    Transformer for converting and extracting features from date columns.
DistrictSubdistrictTransformer
    Transformer for cleaning and standardizing district and subdistrict names.
IngestionPreprocessor
    Transformer for initial data ingestion, column renaming, and filtering.
ProvinceTransformer
    Transformer for cleaning and standardizing province names.
StateToStatusTransformer
    Transformer for mapping raw state values to standardized status codes.

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
from .IngestionPreprocessor import IngestionPreprocessor
from .ProvinceTransformer import ProvinceTransformer
from .StateToStatusTransformer import StateToStatusTransformer

# Define what gets imported with 'from pipelines import *'
__all__ = [
    # Classes
    # AddressTransformer.py
    "AddressTransformer",
    # CleansingPipeline.py
    "CleansingPipeline",
    # CoordinateTransformer.py
    "CoordinateTransformer",
    # DateTransformer.py
    "DateTransformer",
    # DistrictSubdistrictTransformer.py
    "DistrictSubdistrictTransformer",
    # IngestionPreprocessor.py
    "IngestionPreprocessor",
    # ProvinceTransformer.py
    "ProvinceTransformer",
    # StateToStatusTransformer.py
    "StateToStatusTransformer",
]
