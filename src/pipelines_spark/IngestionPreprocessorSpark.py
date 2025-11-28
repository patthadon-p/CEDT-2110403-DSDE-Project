"""
PySpark Transformer for Initial Data Ingestion and Preprocessing.

This module provides the IngestionPreprocessorSpark class, a PySpark ML Transformer
designed for the very first steps of the data pipeline. It handles reading
column configurations (renaming and dropping lists) from a JSON file and
applies these operations (renaming, dropping columns, and filtering rows with NaNs)
directly to the raw input Spark DataFrame.

Classes
-------
IngestionPreprocessorSpark
    A PySpark ML Transformer that renames columns, drops unnecessary columns,
    and filters out rows with missing values based on predefined configuration lists.
"""

# Import necessary modules
import json

from pyspark.ml import Transformer
from pyspark.sql import DataFrame

# Utility Functions
from src.utils.ConfigUtils import read_config_path


class IngestionPreprocessorSpark(Transformer):
    """
    Performs initial data ingestion cleanup (renaming and filtering) on a Spark DataFrame.

    This transformer reads configuration details (column renames, columns to
    drop, and columns to check for null values) from a specified JSON file
    and applies these cleansing steps: **renaming, dropping columns, and dropping rows with NaNs**.

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
    filepath : str
        The resolved absolute path to the configuration file.
    drop_columns : list of str
        The final list of columns to be dropped. Defaults to ["DROP"] if not explicitly set and not found in config.
    drop_na_columns : list of str
        The final list of columns used for filtering (dropping rows with NaNs).
    rename_dict : dict of {str: str}
        Dictionary mapping old column names to new column names.
    """
    
    def __init__(
        self,
        filepath: str = "",
        drop_columns: list[str] | None = None,
        drop_na_columns: list[str] | None = None,
    ) -> None:
        """
        Initializes the transformer by loading configuration parameters from the
        specified JSON file path.

        Parameters
        ----------
        filepath : str, optional
            File path to the JSON file containing the raw data column configurations.
            Default is "".
        drop_columns : list of str or None, optional
            List of columns to be dropped. Default is None.
        drop_na_columns : list of str or None, optional
            List of columns whose rows must not contain NaN/null values. Default is None.
        """

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
        Applies renaming, column dropping, and row filtering based on configuration.

        The transformation performs:
        1. Column renaming.
        2. Dropping specified columns.
        3. Dropping rows where values in `drop_na_columns` are null/NaN.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input raw DataFrame.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with renamed columns, dropped unnecessary columns,
            and filtered rows.
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
