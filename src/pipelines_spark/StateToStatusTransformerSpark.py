"""
State and status column standardization utilities.

This module provides the StateToStatusTransformer class, a Scikit-learn
transformer designed to map raw categorical "state" values to standardized
"status" labels using a lookup dictionary. This ensures consistency in the
target variable or other key categorical features.

Classes
-------
StateToStatusTransformer
    A transformer that renames a column and replaces its values according to a
    predefined mapping dictionary loaded either directly or from a configuration file.
"""

from pyspark.ml import Transformer
from pyspark.sql import DataFrame, SparkSession

from utils.StatusUtils import load_status_mapping


class StateToStatusTransformerSpark(Transformer):
    """
    Maps raw state values to standardized status values and renames the column in a Spark DataFrame.

    Parameters
    ----------
    path : str, optional
        File path for the JSON containing the status mapping. Used only if `mapping` is None.
    mapping : dict or None, optional
        Predefined dictionary ({old_value: new_status}) for mapping. Overrides path if provided.
    old_column : str, optional
        Name of the input column containing raw state values. Default "state".
    new_column : str, optional
        Name of the output column for standardized status values. Default "status".
    """

    def __init__(
        self,
        spark: SparkSession,
        path: str = "",
        mapping: dict | None = None,
        old_column: str | None = None,
        new_column: str | None = None,
    ) -> None:
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
        Applies the mapping and renames the column.
        """
        df_joined = df.join(self.mapping_df, on=self.old_column, how="left")

        if self.new_column != self.old_column:
            df_joined = df_joined.drop(self.old_column)

        return df_joined
