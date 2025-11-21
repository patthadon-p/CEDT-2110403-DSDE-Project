"""
Province name standardization utilities.

This module defines the ProvinceTransformer class, a Scikit-learn transformer
designed to clean and standardize province names in a DataFrame. It uses a
pre-loaded whitelist to map variations (including misspellings and abbreviations)
to their single official name, while tracking any unrecognized values.

It relies on external utility functions for loading the whitelist,
text normalization, and fuzzy string matching.

Classes
-------
ProvinceTransformer
    A transformer that standardizes province names, removing common prefixes
    and mapping variants to official names using a whitelist lookup.
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

from utils.FuzzyUtils import fuzzy_match, normalize
from utils.ProvinceUtils import load_province_whitelist


class ProvinceTransformerSpark(
    Transformer, DefaultParamsReadable, DefaultParamsWritable
):
    """
    Standardizes province names by cleaning prefixes and mapping variants
    to their official standard name using a lookup table (whitelist).

    This transformer performs the following steps on the target column:
    1. **Cleaning:** Removes common prefixes like "จังหวัด" (Province) and "จ." (Abbreviated Province).
    2. **Normalization & Fuzzy Match:** Applies text normalization and attempts to find a match
       in the whitelist keys using fuzzy matching.
    3. **Mapping:** Maps the resulting cleaned name using the loaded whitelist dictionary
       to get the official standard name.
    4. **Filtering:** Collects and stores any original values that could not
       be mapped (i.e., not found in the whitelist) for manual inspection.

    Parameters
    ----------
    path : str, optional
        File path to the JSON file containing the province whitelist mapping.
        Default is "".
    province_column : str or None, optional
        Name of the column containing province names to be transformed.
        Defaults to "province".

    Attributes
    ----------
    path : str
        The file path to the province whitelist used during initialization.
    whitelist : dict of {str: str}
        The loaded reverse lookup dictionary where keys are cleaned/variant names
        and values are the standard official names.
    province_column : str
        The name of the column being processed.
    filtered : list of str
        A running list of all non-standardized (unmapped) province names encountered
        during the transformation process.
    _cache_province : dict
        Internal cache used by the `fuzzy_match` function to store previous
        fuzzy matching results, improving performance.
    """

    def __init__(self, path: str = "", province_column: str | None = None) -> None:
        super().__init__()
        self.path = path
        self.whitelist = load_province_whitelist(self.path)

        self.province_column = province_column or "province"
        self._cache_province = {}

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Transforms the DataFrame by cleaning province names, mapping them
        to standard names, and collecting unmapped variants.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the province column.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with the province column containing
            standardized names (or None if unmapped).
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
