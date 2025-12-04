"""
PySpark Transformer for State-to-Status Mapping.

This module provides the StateToStatusTransformerSpark class, a PySpark ML Transformer
designed to map raw categorical "state" values to standardized "status" labels
by converting the mapping dictionary into a Spark DataFrame and performing a
left join on the input data.

Classes
-------
StateToStatusTransformerSpark
    A PySpark ML Transformer that performs value mapping and column renaming
    using a Spark DataFrame join operation.
"""

# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

# Utility Functions
from src.utils.StatusUtils import load_status_mapping


class StateToStatusTransformerSpark(Transformer):
    """
    Maps raw state values to standardized status values and renames the column in a Spark DataFrame.

    This transformer utilizes the PySpark Join operation:
    1. Converts the lookup `mapping` dictionary into a small PySpark DataFrame (`self.mapping_df`).
    2. Performs a **left join** on the input DataFrame using `old_column` as the key.
    3. The joined DataFrame effectively replaces the values and, if `new_column` is different,
       drops the original `old_column`.

    Parameters
    ----------
    spark : pyspark.sql.SparkSession
        The active SparkSession instance used to create the lookup DataFrame.
    path : str, optional
        File path for the JSON containing the status mapping. Used only if
        `mapping` is None. Default is "".
    mapping : dict or None, optional
        A predefined dictionary ({old_value: new_status}) to use for mapping.
        If provided, this overrides loading from the file path. Default is None.
    old_column : str or None, optional
        Name of the input column containing the raw state values. Defaults to "state".
    new_column : str or None, optional
        Name of the output column for the standardized status values. Defaults to "status".

    Attributes
    ----------
    spark : pyspark.sql.SparkSession
        The active SparkSession instance.
    old_column : str
        The name of the column containing raw input values.
    new_column : str
        The name the column will be renamed to after transformation.
    mapping : dict
        The final dictionary used for value replacement.
    mapping_df : pyspark.sql.DataFrame
        The small PySpark DataFrame derived from `mapping` used for the join operation.
    """

    def __init__(
        self,
        spark: SparkSession,
        path: str = "",
        mapping: dict | None = None,
        old_column: str | None = None,
        new_column: str | None = None,
    ) -> None:
        """
        Initializes the PySpark State-to-Status Transformer and prepares the lookup DataFrame.

        Parameters
        ----------
        spark : pyspark.sql.SparkSession
            The active SparkSession instance used to create the lookup DataFrame.
        path : str, optional
            File path for the JSON containing the status mapping. Default is "".
        mapping : dict or None, optional
            A predefined dictionary ({old_value: new_status}) to use for mapping.
            Default is None.
        old_column : str or None, optional
            Name of the input column containing the raw state values. Defaults to "state".
        new_column : str or None, optional
            Name of the output column for the standardized status values. Defaults to "status".
        """

        super().__init__()

        self.spark = spark

        self.old_column = old_column or "state"
        self.new_column = new_column or "status"
        self.mapping = mapping or load_status_mapping(path)

        mapping_items = list(self.mapping.items())
        self.mapping_df = self.spark.createDataFrame(
            mapping_items, schema=[self.old_column, self.new_column]
        )

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies the state-to-status mapping via a left join and handles column renaming/dropping.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame containing the column with raw state values.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with the target column's values replaced
            by standardized status values.
        """

        df_joined = df.join(self.mapping_df, on=self.old_column, how="left")

        if self.new_column != self.old_column:
            df_joined = df_joined.drop(self.old_column)

        return df_joined
