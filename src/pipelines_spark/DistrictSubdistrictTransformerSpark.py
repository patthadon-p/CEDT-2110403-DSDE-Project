"""
PySpark Transformer for District and Subdistrict Name Standardization.

This module provides the DistrictSubdistrictTransformerSpark class, a PySpark ML Transformer
that cleans, normalizes, and matches district and subdistrict names against a
list of official names using custom logic executed via Spark UDFs (User-Defined Functions)
and fuzzy string matching.

Classes
-------
DistrictSubdistrictTransformerSpark
    A PySpark ML Transformer that standardizes and caches fuzzy matching results
    for district and subdistrict names on a Spark DataFrame.
"""

# Import necessary modules
from pyspark.ml import Transformer
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# Utility Functions
from src.utils.DistrictSubdistrictUtils import load_bangkok_official_area_names
from src.utils.FuzzyUtils import fuzzy_match, normalize


class DistrictSubdistrictTransformerSpark(
    Transformer, DefaultParamsReadable, DefaultParamsWritable
):
    """
    Standardizes and corrects district and subdistrict names in a Spark DataFrame using fuzzy matching.

    The transformation is applied using Spark UDFs, executing the Python `normalize`
    and `fuzzy_match` functions for each row. Results are cached in internal dictionaries
    to optimize repeated matching operations within the Spark driver (though care must
    be taken with UDF caching efficiency in a distributed environment).

    Parameters
    ----------
    path : str, optional
        File path to the JSON file containing the official district and
        subdistrict names (mapping dictionary). Default is "".
    district_column : str or None, optional
        Name of the column containing district names to be transformed. Defaults to "district".
    subdistrict_column : str or None, optional
        Name of the column containing subdistrict names to be transformed. Defaults to "subdistrict".
    cutoff : int or None, optional
        The minimum fuzzy match score required for a name to be accepted. Defaults to 60.
    prefix_bonus : bool or None, optional
        Whether to apply a bonus score for common prefixes during fuzzy matching. Defaults to False.

    Attributes
    ----------
    official_districts : list of str
        The list of standard district names used as fuzzy match targets.
    official_subdistricts : list of str
        The list of standard subdistrict names used as fuzzy match targets.
    cutoff : int
        The minimum fuzzy match score required.
    prefix_bonus : bool
        The status of the prefix bonus setting.
    _cache_district : dict
        Internal dictionary used to cache matched district names (PySpark driver side).
    _cache_subdistrict : dict
        Internal dictionary used to cache matched subdistrict names (PySpark driver side).
    """

    def __init__(
        self,
        path: str = "",
        district_column: str | None = None,
        subdistrict_column: str | None = None,
        cutoff: int | None = None,
        prefix_bonus: bool | None = None,
    ) -> None:
        """
        Initializes the PySpark District/Subdistrict Transformer.

        Loads official area names for use as fuzzy matching targets and initializes caches.

        Parameters
        ----------
        path : str, optional
            File path to the JSON file containing the official area name mapping. Default is "".
        district_column : str or None, optional
            Name of the column containing district names to be transformed. Defaults to "district".
        subdistrict_column : str or None, optional
            Name of the column containing subdistrict names to be transformed. Defaults to "subdistrict".
        cutoff : int or None, optional
            The minimum fuzzy match score required for a name to be accepted. Defaults to 60.
        prefix_bonus : bool or None, optional
            Whether to apply a bonus score for common prefixes during fuzzy matching. Defaults to False.
        """

        super().__init__()
        self.path = path
        self.district_column = district_column or "district"
        self.subdistrict_column = subdistrict_column or "subdistrict"

        self.cutoff = cutoff or 60
        self.prefix_bonus = prefix_bonus if prefix_bonus is not None else False

        official_area_name = load_bangkok_official_area_names(self.path)

        self.official_districts = official_area_name.get("districts", [])
        self.official_subdistricts = official_area_name.get("subdistricts", [])

        self._cache_district = {}
        self._cache_subdistrict = {}

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies name standardization and fuzzy matching via Spark UDFs.

        The transformation overwrites the original district and subdistrict columns
        with the standardized names.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the district and subdistrict columns.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with standardized district and subdistrict names.
        """

        def district_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized,
                self.official_districts,
                self._cache_district,
                cutoff=self.cutoff,
                prefix_bonus=self.prefix_bonus,
            )

        def subdistrict_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized,
                self.official_subdistricts,
                self._cache_subdistrict,
                cutoff=self.cutoff,
                prefix_bonus=self.prefix_bonus,
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
