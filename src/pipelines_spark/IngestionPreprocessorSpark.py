"""
Initial data ingestion and preprocessing utilities.

This module provides the IngestionPreprocessor class, a Scikit-learn transformer
designed for the very first steps of the data pipeline. It handles reading
column configurations (renaming and dropping lists) from a JSON file and
applies these operations directly to the raw input DataFrame.

Classes
-------
IngestionPreprocessor
    A transformer that renames columns, drops unnecessary columns, and filters
    out rows with missing values based on predefined configuration lists.
"""

import json

from pyspark.ml import Transformer
from pyspark.sql import DataFrame

from utils.ConfigUtils import read_config_path


class IngestionPreprocessorSpark(Transformer):
    """
    Performs initial data ingestion cleanup (renaming and filtering).

    This transformer reads configuration details (column renames, columns to
    drop, and columns to check for NaT/null values) from a specified JSON file
    and applies these cleansing steps to the input DataFrame.

    Parameters
    ----------
    filepath : str, optional
        File path to the JSON file containing the raw data column configurations.
        If empty, the path is loaded from the main config file under
        'raw_data_columns_path'. Default is "".
    drop_columns : list of str or None, optional
        List of columns to be dropped. If provided, overrides the list from
        the config file. Default is None.
    drop_na_columns : list of str or None, optional
        List of columns whose rows must not contain NaN/null values. If provided,
        overrides the list from the config file. Default is None.

    Attributes
    ----------
    rename_dict : dict of {str: str}
        Dictionary mapping old column names to new column names.
    drop_columns : list of str
        The final list of columns to be dropped.
    drop_na_columns : list of str
        The final list of columns used for filtering (dropping rows with NaNs).
    """

    def __init__(
        self,
        filepath: str = "",
        drop_columns: list[str] | None = None,
        drop_na_columns: list[str] | None = None,
    ) -> None:

        self.filepath = filepath
        self.drop_columns = drop_columns or []
        self.drop_na_columns = drop_na_columns or []

        if self.filepath == "":
            self.filepath = read_config_path(
                key="raw_data_columns_path", filepath=self.filepath
            )

        with open(self.filepath, encoding="utf-8") as file:
            raw_data_columns = dict(json.load(file))

        self.rename_dict = raw_data_columns.get("columns", {})
        self.drop_columns = (
            drop_columns or raw_data_columns.get("drop_columns", []) or ["DROP"]
        )
        self.drop_na_columns = drop_na_columns or raw_data_columns.get(
            "drop_na_columns", []
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Transforms the DataFrame by renaming, dropping columns, and dropping rows
        with NaNs in specified subsets.

        Parameters
        ----------
        X : pandas.DataFrame
            The input DataFrame (raw data).

        Returns
        -------
        pandas.DataFrame
            The transformed and cleansed DataFrame.
        """

        for old, new in self.rename_dict.items():
            if old in df.columns:
                df = df.withColumnRenamed(old, new)

        actual_drop_cols = [c for c in self.drop_columns if c in df.columns]
        if actual_drop_cols:
            df = df.drop(*actual_drop_cols)

        actual_na_cols = [c for c in self.drop_na_columns if c in df.columns]
        if actual_na_cols:
            df = df.na.drop(subset=actual_na_cols)

        return df
