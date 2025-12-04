"""
PySpark Transformer for Province Name Standardization.

This module provides the ProvinceTransformerSpark class, a PySpark ML Transformer
that cleans, normalizes, and matches raw province names against a predefined
whitelist using regular expressions, Spark UDFs, and fuzzy string matching.

Classes
-------
ProvinceTransformerSpark
    A PySpark ML Transformer that standardizes province names, removes common prefixes,
    and maps variants to their official name, filtering out non-matched records.
"""

# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.ml.util import DefaultParamsReadable, DefaultParamsWritable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# Utility Functions
from src.utils.FuzzyUtils import fuzzy_match, normalize
from src.utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformerSpark(
    Transformer, DefaultParamsReadable, DefaultParamsWritable
):
    """
    Standardizes province names in a Spark DataFrame using cleaning, fuzzy matching, and whitelist mapping.

    The transformation is applied using Spark UDFs and built-in functions, performing the following steps:
    1. **Cleaning:** Removes common prefixes like "จังหวัด" and "จ." (via `regexp_replace`).
    2. **Fuzzy Match:** Uses an internal UDF to normalize the text and find the best match in the whitelist keys (cutoff = 90).
    3. **Mapping & Filtering:** Uses a second UDF to map the matched variant to the standard official name from the whitelist, and filters out rows where no match was found.

    Parameters
    ----------
    path : str, optional
        File path to the JSON file containing the province whitelist mapping. Default is "".
    province_column : str or None, optional
        Name of the column containing province names to be transformed. Defaults to "province".

    Attributes
    ----------
    path : str
        The file path used to load the province whitelist.
    whitelist : dict of {str: str}
        The loaded reverse lookup dictionary where keys are cleaned/variant names
        and values are the standard official names.
    province_column : str
        The final name of the column being processed.
    _cache_province : dict
        Internal cache used by the `fuzzy_match` function (PySpark driver side).
    """

    def __init__(self, path: str = "", province_column: str | None = None) -> None:
        """
        Initializes the PySpark Province Transformer.

        Loads the province whitelist mapping and sets the target column name.

        Parameters
        ----------
        path : str, optional
            File path to the JSON file containing the province whitelist mapping. Default is "".
        province_column : str or None, optional
            Name of the column containing province names to be transformed. Defaults to "province".
        """

        super().__init__()
        self.path = path
        self.whitelist = load_province_whitelist(self.path)

        self.province_column = province_column or "province"
        self._cache_province = {}

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies prefix cleaning, fuzzy matching, whitelist mapping, and filtering.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the province column.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the province column containing
            standardized names, and rows without a valid standardized name filtered out.
        """

        cleaned_df = (
            df.withColumn(
                self.province_column,
                F.regexp_replace(
                    F.col(self.province_column).cast("string"), "จังหวัด", ""
                ),
            )
            .withColumn(
                self.province_column,
                F.regexp_replace(F.col(self.province_column).cast("string"), "จ.", ""),
            )
            .withColumn(self.province_column, F.trim(F.col(self.province_column)))
        )

        def province_udf(x: str | None) -> str | None:
            if x is None:
                return None
            normalized = normalize(x)
            return fuzzy_match(
                normalized, list(self.whitelist.keys()), self._cache_province, cutoff=90
            )

        spark_province_udf = F.udf(province_udf, StringType())

        df_transformed = cleaned_df.withColumn(
            self.province_column,
            spark_province_udf(F.col(self.province_column)),
        )

        def map_to_whitelist(x: str | None) -> str | None:
            return self.whitelist.get(x)

        map_udf = F.udf(map_to_whitelist, StringType())

        df_transformed = df_transformed.withColumn(
            self.province_column, map_udf(F.col(self.province_column))
        )

        df_transformed = df_transformed.filter(F.col(self.province_column).isNotNull())

        return df_transformed
