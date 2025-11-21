"""
District and subdistrict name standardization utilities.

This module provides the DistrictSubdistrictTransformer class, a Scikit-learn
transformer designed to clean, normalize, and match district and subdistrict
names against a list of official names using fuzzy string matching. This
mitigates issues caused by misspellings or inconsistent text input.

Classes
-------
DistrictSubdistrictTransformer
    A transformer that standardizes district and subdistrict names using
    text normalization and caching fuzzy matching against a predefined list
    of official names.
"""

# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.ml import Transformer
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from utils.DistrictSubdistrictUtils import load_bangkok_official_area_names
from utils.FuzzyUtils import fuzzy_match, normalize


class DistrictSubdistrictTransformerSpark(
    Transformer, DefaultParamsReadable, DefaultParamsWritable
):
    """
    Standardizes and corrects district and subdistrict names in a Spark DataFrame.
    """

    def __init__(
        self,
        path: str = "",
        district_column: str | None = None,
        subdistrict_column: str | None = None,
    ) -> None:
        super().__init__()
        self.path = path
        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        official_area_name = load_bangkok_official_area_names(self.path)
        self.official_districts = official_area_name.get("districts", [])
        self.official_subdistricts = official_area_name.get("subdistricts", [])

        self._cache_district = {}
        self._cache_subdistrict = {}

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies normalization and fuzzy matching to district and subdistrict columns.
        """

        def district_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized, self.official_districts, self._cache_district
            )

        def subdistrict_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized, self.official_subdistricts, self._cache_subdistrict
            )

        spark_district_udf = F.udf(district_udf, StringType())
        spark_subdistrict_udf = F.udf(subdistrict_udf, StringType())

        df_transformed = df.withColumn(
            self.district_column,
            spark_district_udf(F.col(self.district_column)),
        ).withColumn(
            self.subdistrict_column,
            spark_subdistrict_udf(F.col(self.subdistrict_column)),
        )

        return df_transformed
