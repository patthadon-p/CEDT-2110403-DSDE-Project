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
# from .AddressTransformer import AddressTransformer
# from .CleansingPipeline import CleansingPipeline
# from .CoordinateTransformer import CoordinateTransformer
from .DateTransformerSpark import DateTransformerSpark
# from .DistrictSubdistrictTransformer import DistrictSubdistrictTransformer
from .IngestionPreprocessorSpark import IngestionPreprocessorSpark
from .ProvinceTransformerSpark import ProvinceTransformerSpark
# from .StateToStatusTransformer import StateToStatusTransformer


# Define what gets imported with 'from pipelines import *'
__all__ = [
    # Classes
    # # AddressTransformer.py
    # "AddressTransformer",
    # # CleansingPipeline.py
    # "CleansingPipeline",
    # # CoordinateTransformer.py
    # "CoordinateTransformer",
    # DateTransformerSpark.py
    "DateTransformerSpark",
    # # DistrictSubdistrictTransformer.py
    # "DistrictSubdistrictTransformer",
    # IngestionPreprocessorSpark.py
    "IngestionPreprocessorSpark",
    # ProvinceTransformerSpark.py
    "ProvinceTransformerSpark",
    # # StateToStatusTransformer.py
    # "StateToStatusTransformer",
]
