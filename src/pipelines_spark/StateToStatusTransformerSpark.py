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

# Setting up the environment
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

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
        path: str = "",
        mapping: dict | None = None,
        old_column: str | None = None,
        new_column: str | None = None,
    ) -> None:
        super().__init__()
        self.old_column = old_column or "state"
        self.new_column = new_column or "status"
        self.mapping = mapping or load_status_mapping(path)

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies the mapping and renames the column.
        """
        mapping_expr = F.create_map(
            [F.lit(x) for kv in self.mapping.items() for x in kv]
        )

        df_transformed = df.withColumn(
            self.new_column, mapping_expr[F.col(self.old_column)]
        )

        if self.new_column != self.old_column:
            df_transformed = df_transformed.drop(self.old_column)

        return df_transformed
