"""
Date feature transformation utilities.

This module provides the DateTransformer class, a Scikit-learn-compatible
transformer designed to clean and standardize date columns in a DataFrame.
It converts columns to datetime format, handles parsing errors, and extracts
useful temporal features (day, month, year) for machine learning models.

Classes
-------
DateTransformer
    A transformer that converts specified columns to datetime objects and
    extracts time-based features, dropping the original column.
"""

import os
import sys

from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, dayofmonth, month, to_timestamp, year

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DateTransformerSpark(Transformer):
    """
    Converts specified columns to datetime objects and extracts new date features.

    For each specified column:
    1. Converts the column to a datetime format (coercing errors to NaT).
    2. Extracts and creates three new integer columns: `_date`, `_month`, and `_year`.
    3. Drops the original datetime column.

    Parameters
    ----------
    columns : list of str or None, optional
        List of column names to transform. Defaults to ["timestamp", "last_activity"].

    Attributes
    ----------
    columns : list of str
        The final list of columns that will be processed.
    """

    def __init__(self, columns: list[str] | None = None) -> None:
        self.columns = columns or ["timestamp", "last_activity"]

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Transforms the DataFrame by standardizing date columns and extracting features.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame containing the date columns to be processed.

        Returns
        -------
        pandas.DataFrame
            The transformed DataFrame with the original date columns replaced
            by the new `_date`, `_month`, and `_year` feature columns.
        """

        for c in self.columns:
            if c in df.columns:
                df = df.withColumn(c, to_timestamp(col(c)))

                df = df.withColumn(f"{c}_date", dayofmonth(col(c)))
                df = df.withColumn(f"{c}_month", month(col(c)))
                df = df.withColumn(f"{c}_year", year(col(c)))

                df = df.drop(c)

        return df
