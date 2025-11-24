"""
PySpark Transformer for Data Filtering and Column Dropping.

This module provides the DataFilterTransformerSpark class, a PySpark ML Transformer
designed for initial or intermediate filtering operations on a Spark DataFrame.
It filters rows based on fixed categorical values and drops columns that are
no longer needed in the subsequent pipeline stages.

Classes
-------
DataFilterTransformerSpark
    A PySpark ML Transformer that filters DataFrame rows based on predefined
    column-value mappings and drops unnecessary columns.
"""

# Import necessary libraries
from pyspark.ml import Transformer
from pyspark.sql import DataFrame
from pyspark.sql.functions import col


class DataFilterTransformerSpark(Transformer):
    """
    Filters a PySpark DataFrame based on fixed categorical values and drops specified columns.

    This transformer is typically used early in the pipeline to limit the dataset
    to a specific scope (e.g., only Bangkok and 'done' statuses) and remove raw/identifier columns.

    Parameters
    ----------
    filter_columns : dict of {str: str} or None, optional
        A dictionary mapping column names to the single value that rows must contain
        (e.g., `{'province': 'กรุงเทพมหานคร'}`). Defaults to filtering 'province' and 'status'.
    drop_columns : list or None, optional
        A list of column names to be permanently dropped from the DataFrame.
        Defaults to removing raw/identifier columns like 'ticket_id', 'comment', 'coords', etc.

    Attributes
    ----------
    filter_columns : dict of {str: str}
        The final dictionary used for row filtering (column: required_value).
    drop_columns : list
        The final list of columns to be dropped.
    """
    
    def __init__(
        self,
        filter_columns: dict[str, str] | None = None,
        drop_columns: list | None = None,
    ) -> None:
        """
        Initializes the PySpark Data Filter Transformer.

        Parameters
        ----------
        filter_columns : dict of {str: str} or None, optional
            A dictionary mapping column names to the single value that rows must contain.
            Defaults to filtering 'province' and 'status'.
        drop_columns : list or None, optional
            A list of column names to be permanently dropped from the DataFrame.
            Defaults to removing raw/identifier columns.
        """
        
        self.filter_columns = filter_columns or {
            "province": "กรุงเทพมหานคร",
            "status": "done",
        }

        self.drop_columns = drop_columns or [
            "ticket_id",
            "comment",
            "coords",
            "address",
        ]

    def _transform(self, df: DataFrame) -> DataFrame:
        """
        Applies row filtering and column dropping to the input DataFrame.

        Rows are filtered based on the values in `filter_columns`. Filtered columns
        are subsequently dropped from the DataFrame.

        Parameters
        ----------
        df : pyspark.sql.DataFrame
            The input DataFrame.

        Returns
        -------
        pyspark.sql.DataFrame
            The transformed DataFrame with filtered rows and dropped columns.
        """
        
        for column, value in self.filter_columns.items():
            if column in df.columns:
                df = df.filter(col(column).isin([value])).drop(column)

        df_transformed = df.drop(*self.drop_columns)

        return df_transformed
