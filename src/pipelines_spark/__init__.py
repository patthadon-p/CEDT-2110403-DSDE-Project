"""
Pipelines Module

This module contains data transformation and processing pipelines
for the CEDT-2110403-DSDE-Project.

Usage:
    # Import everything
    from pipelines import *

    # Import specific classes
    from pipelines import ProvinceTransformerSpark

    # Access directly
    import pipelines
    transformer = pipelines.ProvinceTransformerSpark()
"""

# Import specific classes and functions for direct access
from .AddressEncoderSpark import AddressEncoderSpark
from .AddressTransformerSpark import AddressTransformerSpark
from .CleansingPipelineSpark import CleansingPipelineSpark

# from .CoordinateTransformerSpark import CoordinateTransformerSpark
from .DataFilterTransformerSpark import DataFilterTransformerSpark
from .DateTransformerSpark import DateTransformerSpark
from .DistrictSubdistrictTransformerSpark import DistrictSubdistrictTransformerSpark
from .EncoderPipelineSpark import EncoderPipelineSpark
from .IngestionPreprocessorSpark import IngestionPreprocessorSpark
from .OrganizationEncoderSpark import OrganizationEncoderSpark
from .ProvinceTransformerSpark import ProvinceTransformerSpark
from .ResolutionTimeTransformerSpark import ResolutionTimeTransformerSpark
from .StateToStatusTransformerSpark import StateToStatusTransformerSpark
from .TypeEncoderSpark import TypeEncoderSpark

# Define what gets imported with 'from pipelines import *'
__all__ = [
    # Classes
    # AddressEncoderSpark.py
    "AddressEncoderSpark",
    # AddressTransformerSpark.py
    "AddressTransformerSpark",
    # CleansingPipelineSpark.py
    "CleansingPipelineSpark",
    # # CoordinateTransformer.py
    # "CoordinateTransformer",
    # DataFilterTransformerSpark.py
    "DataFilterTransformerSpark",
    # DateTransformerSpark.py
    "DateTransformerSpark",
    # DistrictSubdistrictTransformerSpark.py
    "DistrictSubdistrictTransformerSpark",
    # EncoderPipelineSpark.py
    "EncoderPipelineSpark",
    # IngestionPreprocessorSpark.py
    "IngestionPreprocessorSpark",
    # OrganizationEncoderSpark.py
    "OrganizationEncoderSpark",
    # ProvinceTransformerSpark.py
    "ProvinceTransformerSpark",
    # ResolutionTimeTransformerSpark.py
    "ResolutionTimeTransformerSpark",
    # StateToStatusTransformerSpark.py
    "StateToStatusTransformerSpark",
    # TypeEncoderSpark.py
    "TypeEncoderSpark",
]
