"""
Pipelines Module

This module contains data transformation and processing pipelines
for the CEDT-2110403-DSDE-Project.

It provides direct access to all major **Spark-based** transformer classes designed
for data cleansing, standardization, feature engineering, and encoding in a
Big Data environment using PySpark.

Classes
-------
AddressEncoderSpark
    A PySpark transformer for encoding standardized address columns into features.
AddressTransformerSpark
    A PySpark meta-transformer that orchestrates address cleaning and enrichment.
CleansingPipelineSpark
    The main PySpark meta-transformer for comprehensive data ingestion and cleansing.
CoordinateTransformerSpark
    A PySpark transformer for validating coordinates and performing spatial joins.
DataFilterTransformerSpark
    A PySpark transformer for filtering rows based on complex criteria.
DateTransformerSpark
    A PySpark transformer for converting date columns and extracting temporal features.
DistrictSubdistrictTransformerSpark
    A PySpark transformer for cleaning and standardizing district/subdistrict names.
EncoderPipelineSpark
    A PySpark meta-pipeline for sequential feature encoding (e.g., StringIndexers/OHE).
IngestionPreprocessorSpark
    A PySpark transformer for initial column renaming and basic filtering.
ModelPrepPipelineSpark
    A PySpark meta-pipeline combining all transformation and encoding steps for model consumption.
OrganizationEncoderSpark
    A PySpark transformer for encoding the organization column.
ProvinceTransformerSpark
    A PySpark transformer for cleaning and standardizing province names.
ResolutionTimeTransformerSpark
    A PySpark transformer for calculating and transforming event resolution time features.
StateToStatusTransformerSpark
    A PySpark transformer for mapping raw state values to standardized status codes.
TypeEncoderSpark
    A PySpark transformer for encoding the problem type column.

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
from .CoordinateTransformerSpark import CoordinateTransformerSpark
from .DataFilterTransformerSpark import DataFilterTransformerSpark
from .DateTransformerSpark import DateTransformerSpark
from .DistrictSubdistrictTransformerSpark import DistrictSubdistrictTransformerSpark
from .EncoderPipelineSpark import EncoderPipelineSpark
from .IngestionPreprocessorSpark import IngestionPreprocessorSpark
from .ModelDefinePipelineSpark import ModelDefinePipelineSpark
from .ModelPrepPipelineSpark import ModelPrepPipelineSpark
from .OrganizationEncoderSpark import OrganizationEncoderSpark
from .ProvinceTransformerSpark import ProvinceTransformerSpark
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
    # CoordinateTransformerSpark.py
    "CoordinateTransformerSpark",
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
    # ModelDefinePipelineSpark.py
    "ModelDefinePipelineSpark",
    # ModelPrepPipelineSpark.py
    "ModelPrepPipelineSpark",
    # OrganizationEncoderSpark.py
    "OrganizationEncoderSpark",
    # ProvinceTransformerSpark.py
    "ProvinceTransformerSpark",
    # StateToStatusTransformerSpark.py
    "StateToStatusTransformerSpark",
    # TypeEncoderSpark.py
    "TypeEncoderSpark",
]
